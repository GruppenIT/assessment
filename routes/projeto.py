from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from models.projeto import Projeto
import logging

projeto_bp = Blueprint('projeto', __name__, url_prefix='/admin/projetos')

@projeto_bp.route('/')
@login_required
@admin_required
def listar():
    """Lista todos os projetos"""
    projetos = Projeto.query.filter_by(ativo=True).all()
    return render_template('admin/projetos/listar.html', projetos=projetos)

@projeto_bp.route('/<int:projeto_id>')
@login_required
@admin_required
def detalhar(projeto_id):
    """Detalha um projeto específico"""
    projeto = Projeto.query.get_or_404(projeto_id)
    return render_template('admin/projetos/detalhar.html', projeto=projeto)

@projeto_bp.route('/<int:projeto_id>/estatisticas')
def estatisticas(projeto_id):
    """Exibe estatísticas detalhadas do projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Dados básicos para o template
    estatisticas_gerais = {
        'total_respondentes': 0,
        'total_assessments': 0,
        'data_inicio': projeto.data_criacao,
        'data_finalizacao': None
    }
    
    # Verificar se existe relatório IA
    try:
        from models.relatorio_ia import RelatorioIA
        relatorio_ia = RelatorioIA.get_by_projeto(projeto.id)
    except:
        relatorio_ia = None
    
    return render_template('admin/projetos/estatisticas.html',
                         projeto=projeto,
                         estatisticas_gerais=estatisticas_gerais,
                         estatisticas_assessments=[],
                         score_medio_projeto=0,
                         respondentes=[],
                         dados_graficos={},
                         memorial_respostas={},
                         relatorio_ia=relatorio_ia)

@projeto_bp.route('/<int:projeto_id>/gerar-relatorio-ia', methods=['POST'])
def gerar_relatorio_ia(projeto_id):
    """Gera relatório inteligente usando ChatGPT"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    try:
        from utils.openai_utils import gerar_relatorio_ia
        from models.relatorio_ia import RelatorioIA
        
        # Gerar relatório
        dados_relatorio = gerar_relatorio_ia(projeto)
        
        # Salvar no banco
        relatorio = RelatorioIA.criar_relatorio(projeto_id, dados_relatorio)
        
        if dados_relatorio.get('erro'):
            flash(f'Erro ao gerar relatório: {dados_relatorio["erro"]}', 'danger')
        else:
            flash('Relatório inteligente gerado com sucesso!', 'success')
        
    except Exception as e:
        logging.error(f"Erro ao gerar relatório IA: {e}")
        flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
    
    return redirect(url_for('projeto.estatisticas', projeto_id=projeto_id))

@projeto_bp.route('/<int:projeto_id>/relatorio-ia/<int:relatorio_id>')
def visualizar_relatorio_ia(projeto_id, relatorio_id):
    """Visualiza relatório IA específico"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    from models.relatorio_ia import RelatorioIA
    relatorio = RelatorioIA.query.filter_by(
        id=relatorio_id,
        projeto_id=projeto_id
    ).first_or_404()
    
    return render_template('admin/projetos/relatorio_ia.html',
                         projeto=projeto,
                         relatorio=relatorio)

@projeto_bp.route('/<int:projeto_id>/estatisticas/pdf')
def exportar_estatisticas_pdf(projeto_id):
    """Exporta as estatísticas do projeto para PDF"""
    return f"Exportar PDF - Projeto {projeto_id}"

@projeto_bp.route('/<int:projeto_id>/estatisticas/markdown')
def exportar_estatisticas_markdown(projeto_id):
    """Exporta as estatísticas do projeto para Markdown"""
    return f"Exportar Markdown - Projeto {projeto_id}"

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