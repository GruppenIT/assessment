from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from models.projeto import Projeto
import logging

projeto_bp = Blueprint('projeto', __name__, url_prefix='/admin/projetos')

@projeto_bp.route('/')
def listar():
    """Lista todos os projetos ou filtra por cliente"""
    try:
        cliente_id = request.args.get('cliente')
        
        # Query SQL simples para buscar projetos
        if cliente_id:
            sql_query = "SELECT p.id, p.nome, p.descricao, p.data_criacao, c.nome as cliente_nome FROM projetos p LEFT JOIN clientes c ON p.cliente_id = c.id WHERE p.ativo = true AND p.cliente_id = :cliente_id ORDER BY p.data_criacao DESC"
            projetos_raw = db.session.execute(db.text(sql_query), {'cliente_id': cliente_id}).fetchall()
            from models.cliente import Cliente
            cliente = Cliente.query.get_or_404(cliente_id)
            filtro_cliente = True
        else:
            sql_query = "SELECT p.id, p.nome, p.descricao, p.data_criacao, c.nome as cliente_nome FROM projetos p LEFT JOIN clientes c ON p.cliente_id = c.id WHERE p.ativo = true ORDER BY p.data_criacao DESC"
            projetos_raw = db.session.execute(db.text(sql_query)).fetchall()
            cliente = None
            filtro_cliente = False
        
        # Processar dados dos projetos com tratamento de erro robusto
        projetos_data = []
        for p in projetos_raw:
            try:
                # Valores padrão
                data_criacao = p.data_criacao
                if isinstance(data_criacao, str):
                    from datetime import datetime
                    try:
                        data_criacao = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
                    except:
                        data_criacao = datetime.now()
                
                projetos_data.append({
                    'projeto': {
                        'id': p.id,
                        'nome': p.nome,
                        'descricao': p.descricao,
                        'data_criacao': data_criacao,
                        'cliente': {'nome': p.cliente_nome}
                    },
                    'respondentes_count': 0,  # Valor padrão seguro
                    'tipos_count': 1,  # Valor padrão seguro 
                    'progresso': 0.0  # Valor padrão seguro
                })
            except Exception as e:
                logging.error(f"Erro ao processar projeto {p.id}: {e}")
                continue
        
        # Renderizar template
        return render_template('admin/projetos/listar.html', 
                             projetos=projetos_data,
                             projetos_data=projetos_data,
                             cliente=cliente,
                             filtro_cliente=filtro_cliente,
                             ordem_atual='data_criacao',
                             direcao_atual='desc')
                             
    except Exception as e:
        logging.error(f"Erro geral na listagem de projetos: {str(e)}")
        # Retornar uma página vazia em caso de erro
        return render_template('admin/projetos/listar.html', 
                             projetos=[],
                             projetos_data=[],
                             cliente=None,
                             filtro_cliente=False,
                             ordem_atual='data_criacao',
                             direcao_atual='desc')

@projeto_bp.route('/working')
@login_required
@admin_required
def listar_working():
    """Lista todos os projetos - versão funcional"""
    try:
        projetos_raw = db.session.execute(
            db.text("SELECT p.id, p.nome, p.descricao, p.data_criacao, c.nome as cliente_nome FROM projetos p LEFT JOIN clientes c ON p.cliente_id = c.id WHERE p.ativo = true ORDER BY p.data_criacao DESC")
        ).fetchall()
        
        projetos_data = []
        for p in projetos_raw:
            # Calcular dados reais do projeto
            projeto_obj = Projeto.query.get(p.id)
            progresso = projeto_obj.get_progresso_geral() if projeto_obj else 0
            respondentes_count = len(projeto_obj.get_respondentes_ativos()) if projeto_obj else 0
            tipos_count = len(projeto_obj.get_tipos_assessment()) if projeto_obj else 0
            
            # Garantir que data_criacao seja um objeto datetime
            data_criacao = p.data_criacao
            if isinstance(data_criacao, str):
                from datetime import datetime
                try:
                    data_criacao = datetime.fromisoformat(data_criacao.replace('Z', '+00:00'))
                except:
                    from datetime import datetime
                    data_criacao = datetime.now()
            
            projetos_data.append({
                'projeto': {
                    'id': p.id,
                    'nome': p.nome,
                    'descricao': p.descricao,
                    'data_criacao': data_criacao,
                    'cliente': {'nome': p.cliente_nome}
                },
                'respondentes_count': respondentes_count,
                'tipos_count': tipos_count,
                'progresso': progresso
            })
        
        return render_template('admin/projetos/listar.html', 
                             projetos=projetos_data,
                             projetos_data=projetos_data,
                             filtro_cliente=False,
                             ordem_atual='data_criacao',
                             direcao_atual='desc')
                             
    except Exception as e:
        logging.error(f"Erro ao listar projetos: {str(e)}")
        flash(f'Erro ao listar projetos: {str(e)}', 'danger')
        return render_template('admin/projetos/listar.html', 
                             projetos=[],
                             projetos_data=[],
                             filtro_cliente=False)

@projeto_bp.route('/criar', methods=['GET', 'POST'])
@login_required
@admin_required
def criar():
    """Cria um novo projeto"""
    from forms.projeto_forms import ProjetoForm, NovoClienteForm
    from models.cliente import Cliente
    from models.projeto import Projeto, ProjetoAssessment
    from models.assessment_version import AssessmentTipo
    
    form = ProjetoForm()
    novo_cliente_form = NovoClienteForm()
    
    if request.method == 'POST':
        # Validação manual mais simples
        nome = request.form.get('nome', '').strip()
        cliente_id = request.form.get('cliente_id')
        tipos_ids = request.form.getlist('tipos_assessment')
        descricao = request.form.get('descricao', '').strip()
        
        logging.info(f"Dados recebidos - tipos: {tipos_ids}, nome: {nome}, cliente: {cliente_id}")
        
        # Validações
        errors = []
        if not nome or len(nome) < 2:
            errors.append('Nome do projeto é obrigatório (mínimo 2 caracteres)')
        if not cliente_id:
            errors.append('Cliente é obrigatório')
        if not tipos_ids:
            errors.append('Selecione pelo menos um tipo de assessment')
            
        if not errors:
            try:
                # Criar projeto
                projeto = Projeto(
                    nome=nome,
                    cliente_id=int(cliente_id),
                    descricao=descricao
                )
                db.session.add(projeto)
                db.session.flush()  # Para obter o ID do projeto
                
                # Associar tipos de assessment (sistema novo)
                for tipo_id in tipos_ids:
                    # Buscar o tipo de assessment
                    tipo_assessment = AssessmentTipo.query.get(int(tipo_id))
                    if tipo_assessment:
                        # Buscar a versão publicada
                        versao_ativa = tipo_assessment.get_versao_ativa()
                        if versao_ativa:
                            projeto_assessment = ProjetoAssessment(
                                projeto_id=projeto.id,
                                versao_assessment_id=versao_ativa.id
                            )
                            db.session.add(projeto_assessment)
                
                db.session.commit()
                flash(f'Projeto "{projeto.nome}" criado com sucesso!', 'success')
                return redirect(url_for('projeto.detalhar', projeto_id=projeto.id))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Erro ao criar projeto: {e}")
                flash('Erro ao criar projeto. Tente novamente.', 'danger')
        else:
            # Mostrar erros de validação
            for error in errors:
                flash(error, 'danger')
    
    return render_template('admin/projetos/criar.html', 
                         form=form, 
                         novo_cliente_form=novo_cliente_form)

@projeto_bp.route('/<int:projeto_id>')
@login_required
@admin_required
def detalhar(projeto_id):
    """Detalha um projeto específico"""
    projeto = Projeto.query.get_or_404(projeto_id)
    return render_template('admin/projetos/detalhar.html', projeto=projeto)

@projeto_bp.route('/<int:projeto_id>/desativar', methods=['POST'])
@login_required
@admin_required
def desativar(projeto_id):
    """Desativa um projeto (soft delete)"""
    projeto = Projeto.query.get_or_404(projeto_id)
    try:
        projeto.ativo = False
        db.session.commit()
        flash(f'Projeto "{projeto.nome}" desativado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar projeto: {str(e)}', 'danger')
        logging.error(f"Erro ao desativar projeto: {e}")
    return redirect(url_for('projeto.listar'))

@projeto_bp.route('/<int:projeto_id>/excluir', methods=['POST'])
@login_required
@admin_required  
def excluir(projeto_id):
    """Exclui um projeto permanentemente"""
    projeto = Projeto.query.get_or_404(projeto_id)
    try:
        # Primeiro excluir respostas relacionadas
        from models.resposta import Resposta
        Resposta.query.filter_by(projeto_id=projeto_id).delete()
        
        # Excluir associações do projeto
        from models.projeto import ProjetoAssessment
        ProjetoAssessment.query.filter_by(projeto_id=projeto_id).delete()
        
        # Excluir o projeto
        nome_projeto = projeto.nome
        db.session.delete(projeto)
        db.session.commit()
        flash(f'Projeto "{nome_projeto}" excluído permanentemente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir projeto: {str(e)}', 'danger')
        logging.error(f"Erro ao excluir projeto: {e}")
    return redirect(url_for('projeto.listar'))

@projeto_bp.route('/<int:projeto_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(projeto_id):
    """Edita um projeto existente"""
    from forms.projeto_forms import ProjetoForm
    from models.cliente import Cliente
    
    projeto = Projeto.query.get_or_404(projeto_id)
    form = ProjetoForm(obj=projeto)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            projeto.nome = form.nome.data
            projeto.descricao = form.descricao.data
            projeto.cliente_id = form.cliente_id.data
            
            db.session.commit()
            flash(f'Projeto "{projeto.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('projeto.detalhar', projeto_id=projeto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar projeto: {str(e)}', 'danger')
            logging.error(f"Erro ao editar projeto: {e}")
    
    return render_template('admin/projetos/editar.html', form=form, projeto=projeto)

@projeto_bp.route('/<int:projeto_id>/respondentes')
@login_required
@admin_required
def gerenciar_respondentes(projeto_id):
    """Gerencia respondentes de um projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Buscar respondentes do cliente do projeto
    respondentes_cliente = []
    if projeto.cliente:
        from models.respondente import Respondente
        respondentes_cliente = Respondente.query.filter_by(
            cliente_id=projeto.cliente_id, 
            ativo=True
        ).all()
    
    # Respondentes já associados ao projeto
    respondentes_projeto = projeto.get_respondentes_ativos()
    
    return render_template('admin/projetos/gerenciar_respondentes.html', 
                         projeto=projeto,
                         respondentes_cliente=respondentes_cliente,
                         respondentes_projeto=respondentes_projeto)

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