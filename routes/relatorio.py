from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from app import db
from models.usuario import Usuario
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from utils.auth_utils import admin_or_owner_required
from utils.pdf_utils import gerar_pdf_relatorio
import json
from datetime import datetime

relatorio_bp = Blueprint('relatorio', __name__)

@relatorio_bp.route('/visualizar/<int:usuario_id>')
@login_required
@admin_or_owner_required
def visualizar(usuario_id):
    """Visualiza o relatório de um assessment"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if not usuario.assessment_concluido():
        flash('O assessment ainda não foi concluído.', 'warning')
        if current_user.is_admin():
            return redirect(url_for('admin.assessments'))
        else:
            return redirect(url_for('cliente.dashboard'))
    
    # Buscar todas as respostas do usuário
    respostas = Resposta.query.filter_by(usuario_id=usuario_id).join(
        Pergunta
    ).join(Dominio).order_by(
        Dominio.ordem, Pergunta.ordem
    ).all()
    
    # Organizar dados por domínio
    dados_dominios = {}
    for resposta in respostas:
        dominio_nome = resposta.pergunta.dominio.nome
        
        if dominio_nome not in dados_dominios:
            dados_dominios[dominio_nome] = {
                'dominio': resposta.pergunta.dominio,
                'respostas': [],
                'notas': [],
                'media': 0
            }
        
        dados_dominios[dominio_nome]['respostas'].append(resposta)
        dados_dominios[dominio_nome]['notas'].append(resposta.nota)
    
    # Calcular médias por domínio
    for dominio_nome, dados in dados_dominios.items():
        if dados['notas']:
            dados['media'] = round(sum(dados['notas']) / len(dados['notas']), 2)
    
    # Calcular média geral
    todas_notas = [resposta.nota for resposta in respostas]
    media_geral = round(sum(todas_notas) / len(todas_notas), 2) if todas_notas else 0
    
    # Preparar dados para gráfico
    labels_grafico = list(dados_dominios.keys())
    dados_grafico = [dados_dominios[label]['media'] for label in labels_grafico]
    
    return render_template('relatorio/visualizar.html',
                         usuario=usuario,
                         dados_dominios=dados_dominios,
                         media_geral=media_geral,
                         total_respostas=len(respostas),
                         labels_grafico=json.dumps(labels_grafico),
                         dados_grafico=json.dumps(dados_grafico),
                         data_relatorio=datetime.now())

@relatorio_bp.route('/pdf/<int:usuario_id>')
@login_required
@admin_or_owner_required
def gerar_pdf(usuario_id):
    """Gera relatório em PDF"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if not usuario.assessment_concluido():
        flash('O assessment ainda não foi concluído.', 'warning')
        return redirect(url_for('relatorio.visualizar', usuario_id=usuario_id))
    
    try:
        # Gerar PDF
        pdf_content = gerar_pdf_relatorio(usuario_id)
        
        # Criar resposta HTTP
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=relatorio_assessment_{usuario.nome_empresa}_{usuario.id}.pdf'
        
        return response
    
    except Exception as e:
        flash('Erro ao gerar relatório PDF.', 'danger')
        return redirect(url_for('relatorio.visualizar', usuario_id=usuario_id))

@relatorio_bp.route('/exportar/<int:usuario_id>')
@login_required
@admin_or_owner_required
def exportar_html(usuario_id):
    """Exporta relatório em HTML"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    if not usuario.assessment_concluido():
        flash('O assessment ainda não foi concluído.', 'warning')
        return redirect(url_for('relatorio.visualizar', usuario_id=usuario_id))
    
    # Redirecionar para visualização (que já é em HTML)
    return redirect(url_for('relatorio.visualizar', usuario_id=usuario_id))
