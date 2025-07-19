from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from forms.projeto_forms import ProjetoForm, NovoClienteForm, AdicionarRespondenteForm
# Alias para compatibilidade
ProjetoResponenteForm = AdicionarRespondenteForm
from models.projeto import Projeto, ProjetoRespondente, ProjetoAssessment
from models.cliente import Cliente
from models.respondente import Respondente
from models.tipo_assessment import TipoAssessment
from models.assessment_version import AssessmentTipo, AssessmentVersao, AssessmentDominio
from models.dominio import Dominio
from models.pergunta import Pergunta
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
    cliente_id = request.args.get('cliente')
    
    if cliente_id:
        # Filtrar projetos por cliente específico
        try:
            cliente = Cliente.query.get_or_404(cliente_id)
            projetos_raw = db.session.execute(
                db.text("SELECT p.id, p.nome, p.descricao, p.data_criacao, c.nome as cliente_nome FROM projetos p LEFT JOIN clientes c ON p.cliente_id = c.id WHERE p.ativo = true AND p.cliente_id = :cliente_id ORDER BY p.data_criacao DESC"),
                {'cliente_id': cliente_id}
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
                                 cliente=cliente,
                                 filtro_cliente=True,
                                 ordem_atual='data_criacao',
                                 direcao_atual='desc')
        except Exception as e:
            logging.error(f"Erro ao filtrar projetos: {str(e)}")
            flash(f'Erro ao filtrar projetos: {str(e)}', 'danger')
            return redirect(url_for('projeto.listar_working'))
    else:
        # Listar todos os projetos - redireciona para versão working
        return redirect(url_for('projeto.listar_working'))

@projeto_bp.route('/criar', methods=['GET', 'POST'])
@login_required
@admin_required
def criar():
    """Cria um novo projeto"""
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
                from models.assessment_version import AssessmentTipo
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

@projeto_bp.route('/criar-cliente', methods=['POST'])
@login_required
@admin_required
def criar_cliente():
    """Cria um novo cliente durante a criação do projeto"""
    form = NovoClienteForm()
    
    if form.validate_on_submit():
        try:
            cliente = Cliente(
                nome=form.nome.data,
                razao_social=form.nome.data,  # Usar mesmo nome inicialmente
                ativo=True
            )
            db.session.add(cliente)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'cliente_id': cliente.id,
                'cliente_nome': cliente.nome,
                'message': f'Cliente "{cliente.nome}" criado com sucesso!'
            })
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao criar cliente: {e}")
            return jsonify({
                'success': False,
                'message': 'Erro ao criar cliente. Tente novamente.'
            })
    
    return jsonify({
        'success': False,
        'message': 'Dados inválidos.',
        'errors': form.errors
    })

@projeto_bp.route('/<int:projeto_id>')
@login_required
@admin_required
def detalhar(projeto_id):
    """Detalha um projeto específico"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Dados do projeto
    progresso = projeto.get_progresso_geral()
    respondentes = projeto.get_respondentes_ativos()
    tipos_assessment = projeto.get_tipos_assessment()
    
    # Progresso por tipo de assessment (colaborativo)
    progressos_por_tipo = {}
    assessments_com_versao = {}
    
    for projeto_assessment in projeto.assessments:
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        from models.resposta import Resposta
        
        # Determinar tipo e versão do assessment
        tipo = None
        versao_info = "Sistema Antigo"
        
        if projeto_assessment.versao_assessment_id:
            # Novo sistema de versionamento
            versao = projeto_assessment.versao_assessment
            tipo = versao.tipo
            versao_info = f"Versão {versao.versao}"
        elif projeto_assessment.tipo_assessment_id:
            # Sistema antigo
            tipo = projeto_assessment.tipo_assessment
            versao_info = "Sistema Antigo"
        
        # Pular se não conseguir determinar o tipo
        if not tipo:
            continue
        
        if projeto_assessment.versao_assessment_id:
            # Novo sistema de versionamento
            from models.assessment_version import AssessmentDominio
            
            versao = projeto_assessment.versao_assessment
            total_perguntas = db.session.query(Pergunta).join(
                AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
            ).filter(
                AssessmentDominio.versao_id == versao.id,
                AssessmentDominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            # Contar perguntas únicas respondidas (colaborativo)
            perguntas_respondidas = db.session.query(Pergunta.id).join(
                Resposta, Pergunta.id == Resposta.pergunta_id
            ).join(
                AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
            ).filter(
                Resposta.projeto_id == projeto.id,
                AssessmentDominio.versao_id == versao.id,
                AssessmentDominio.ativo == True,
                Pergunta.ativo == True
            ).distinct().count()
        else:
            # Sistema antigo
            total_perguntas = Pergunta.query.join(Dominio).filter(
                Dominio.tipo_assessment_id == tipo.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            # Contar perguntas únicas respondidas (colaborativo)
            perguntas_respondidas = db.session.query(Pergunta.id).join(
                Resposta, Pergunta.id == Resposta.pergunta_id
            ).join(Dominio).filter(
                Resposta.projeto_id == projeto.id,
                Dominio.tipo_assessment_id == tipo.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).distinct().count()
        
        progresso_tipo = round((perguntas_respondidas / total_perguntas * 100) if total_perguntas > 0 else 0, 1)
        
        progressos_por_tipo[tipo.id] = {
            'tipo': tipo,
            'progresso': progresso_tipo,
            'perguntas_respondidas': perguntas_respondidas,
            'total_perguntas': total_perguntas,
            'versao': versao_info
        }
    
    return render_template('admin/projetos/detalhar.html',
                         projeto=projeto,
                         progresso=progresso,
                         respondentes=respondentes,
                         tipos_assessment=tipos_assessment,
                         progressos_por_tipo=progressos_por_tipo)

@projeto_bp.route('/<int:projeto_id>/estatisticas')
@login_required
@admin_required
def estatisticas(projeto_id):
    """Exibe estatísticas detalhadas do projeto finalizado"""
    try:
        projeto = Projeto.query.get_or_404(projeto_id)
        
        # Verificar se projeto está totalmente finalizado
        finalizados, total_assessments = projeto.get_assessments_finalizados()
        totalmente_finalizado = projeto.is_totalmente_finalizado()
        
        if not totalmente_finalizado:
            flash('As estatísticas completas só estão disponíveis quando todos os assessments estão finalizados.', 'warning')
            return redirect(url_for('projeto.detalhar', projeto_id=projeto.id))
        
        # Dados básicos para template
        respondentes = projeto.get_respondentes_ativos()
        
        # Dados mínimos para não quebrar o template
        estatisticas_gerais = {
            'total_respondentes': len(respondentes),
            'total_assessments': total_assessments,
            'data_inicio': projeto.data_criacao,
            'data_finalizacao': projeto.data_finalizacao or projeto.data_criacao
        }
        
        estatisticas_assessments = []
        score_medio_projeto = 0
        dados_graficos = {'radar': {}, 'scores_assessments': {}}
        memorial_respostas = {}
        relatorio_ia = None
        
        return render_template('admin/projetos/estatisticas.html',
                             projeto=projeto,
                             estatisticas_gerais=estatisticas_gerais,
                             estatisticas_assessments=estatisticas_assessments,
                             score_medio_projeto=score_medio_projeto,
                             respondentes=respondentes,
                             dados_graficos=dados_graficos,
                             memorial_respostas=memorial_respostas,
                             relatorio_ia=relatorio_ia)
    
    except Exception as e:
        logging.error(f"Erro na função estatísticas: {e}")
        flash(f'Erro ao carregar estatísticas: {str(e)}', 'danger')
        return redirect(url_for('projeto.detalhar', projeto_id=projeto_id))

@projeto_bp.route('/<int:projeto_id>/gerar-introducao-ia', methods=['POST'])
@login_required

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
