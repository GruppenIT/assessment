from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from utils.auth_utils import admin_required
from models.projeto import Projeto, ProjetoRespondente, ProjetoAssessment
from models.cliente import Cliente
from models.respondente import Respondente
from models.assessment_version import AssessmentTipo, AssessmentVersao, AssessmentDominio
from models.tipo_assessment import TipoAssessment
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from forms.projeto_forms import ProjetoForm
from forms.cliente_forms import NovoClienteForm
from app import db
from models.resposta import Resposta
from werkzeug.security import generate_password_hash
from sqlalchemy import func, case, and_
import logging
import json
from datetime import datetime

projeto_bp = Blueprint('projeto', __name__, url_prefix='/admin/projetos')

@projeto_bp.route('/auto-login')
def auto_login():
    """Auto login para teste"""
    from flask_login import login_user
    from models.usuario import Usuario
    from flask import session
    
    admin = Usuario.query.filter_by(email='admin@sistema.com').first()
    if admin:
        login_user(admin)
        session['user_type'] = 'admin'
        return redirect(url_for('projeto.listar'))
    else:
        return "Admin não encontrado"

@projeto_bp.route('/working')
def listar_working():
    """Lista todos os projetos - versão simplificada"""
    try:
        from models.projeto import Projeto
        from models.cliente import Cliente
        
        projetos_data = []
        projetos = Projeto.query.filter_by(ativo=True).all()
        
        for projeto in projetos:
            progresso = projeto.get_progresso_geral()
            respondentes_count = len(projeto.get_respondentes_ativos())
            tipos_count = len(projeto.get_tipos_assessment())
            
            projetos_data.append({
                'projeto': projeto,
                'respondentes_count': respondentes_count,
                'tipos_count': tipos_count,
                'progresso': progresso
            })

        return render_template('admin/projetos/listar.html', 
                             projetos=projetos_data,
                             projetos_data=projetos_data,
                             ordem_atual='data_criacao',
                             direcao_atual='desc')
        
    except Exception as e:
        return f"<h1>Erro ao carregar projetos: {str(e)}</h1>"

@projeto_bp.route('/')
def listar():
    """Lista todos os projetos ou filtra por cliente"""
    return redirect(url_for('projeto.listar_working'))

@projeto_bp.route('/<int:projeto_id>/estatisticas')
@login_required
@admin_required
def estatisticas(projeto_id):
    """Teste de rota simples"""
    return f"<h1>Teste - Projeto ID: {projeto_id}</h1>"

@projeto_bp.route('/<int:projeto_id>/gerar-introducao-ia', methods=['POST'])
@login_required
@admin_required
def gerar_introducao_ia(projeto_id):
    """Gera introdução do relatório usando ChatGPT"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se projeto está totalmente finalizado
    if not projeto.is_totalmente_finalizado():
        flash('A introdução IA só pode ser gerada quando todos os assessments estão finalizados.', 'warning')
        return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))
    
    try:
        from utils.openai_utils import gerar_introducao_ia
        
        # Gerar introdução
        resultado = gerar_introducao_ia(projeto)
        
        if resultado.get('erro'):
            flash(f'Erro ao gerar introdução: {resultado["erro"]}', 'danger')
        else:
            # Salvar no banco
            projeto.introducao_ia = resultado['introducao']
            db.session.commit()
            flash('Introdução inteligente gerada com sucesso!', 'success')
        
    except Exception as e:
        logging.error(f"Erro ao gerar introdução IA: {e}")
        flash(f'Erro ao gerar introdução: {str(e)}', 'danger')
    
    return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))