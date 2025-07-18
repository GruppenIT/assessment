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
    """Inicia a geração do relatório inteligente usando ChatGPT"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    from flask import session
    import threading
    import uuid
    
    # Gerar ID único para o processo
    task_id = str(uuid.uuid4())
    _task_storage[task_id] = {
        'status': 'iniciado',
        'progresso': 0,
        'mensagem': 'Inicializando geração do relatório...',
        'projeto_id': projeto_id
    }
    
    # Iniciar processo em thread separada
    thread = threading.Thread(target=_gerar_relatorio_background, args=(projeto_id, task_id))
    thread.daemon = True
    thread.start()
    
    return redirect(url_for('projeto.progresso_relatorio_ia', projeto_id=projeto_id, task_id=task_id))

# Armazenamento global para tasks (em produção, use Redis ou banco de dados)
_task_storage = {}

def _gerar_relatorio_background(projeto_id, task_id):
    """Gera relatório em background com atualizações de progresso"""
    from app import app
    
    with app.app_context():
        try:
            from utils.openai_utils import gerar_relatorio_ia
            from models.relatorio_ia import RelatorioIA
            from models.projeto import Projeto
            
            projeto = Projeto.query.get(projeto_id)
            
            # Atualizar progresso
            _task_storage[task_id] = {
                'status': 'processando',
                'progresso': 20,
                'mensagem': 'Coletando dados do projeto...',
                'projeto_id': projeto_id
            }
            
            # Função de callback para atualizações de progresso
            def update_progress(step, message):
                _task_storage[task_id]['progresso'] = step
                _task_storage[task_id]['mensagem'] = message
            
            # Gerar relatório
            dados_relatorio = gerar_relatorio_ia(projeto, callback_progress=update_progress)
            
            _task_storage[task_id]['progresso'] = 80
            _task_storage[task_id]['mensagem'] = 'Salvando relatório no banco de dados...'
            
            # Salvar no banco
            relatorio = RelatorioIA.criar_relatorio(projeto_id, dados_relatorio)
            
            if dados_relatorio.get('erro'):
                _task_storage[task_id]['status'] = 'erro'
                _task_storage[task_id]['mensagem'] = f'Erro: {dados_relatorio["erro"]}'
            else:
                _task_storage[task_id]['status'] = 'concluido'
                _task_storage[task_id]['progresso'] = 100
                _task_storage[task_id]['mensagem'] = 'Relatório gerado com sucesso!'
                _task_storage[task_id]['relatorio_id'] = relatorio.id
                
        except Exception as e:
            _task_storage[task_id]['status'] = 'erro'
            _task_storage[task_id]['mensagem'] = f'Erro inesperado: {str(e)}'

@projeto_bp.route('/<int:projeto_id>/relatorio-ia/progresso/<task_id>')
def progresso_relatorio_ia(projeto_id, task_id):
    """Exibe página de progresso do relatório IA"""
    projeto = Projeto.query.get_or_404(projeto_id)
    return render_template('admin/projetos/progresso_relatorio_ia.html',
                         projeto=projeto,
                         task_id=task_id)

@projeto_bp.route('/<int:projeto_id>/relatorio-ia/status/<task_id>')
def status_relatorio_ia(projeto_id, task_id):
    """Retorna status atual do relatório IA (AJAX)"""
    from flask import jsonify
    
    task_data = _task_storage.get(task_id, {})
    
    return jsonify({
        'status': task_data.get('status', 'desconhecido'),
        'progresso': task_data.get('progresso', 0),
        'mensagem': task_data.get('mensagem', 'Processando...'),
        'relatorio_id': task_data.get('relatorio_id')
    })

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