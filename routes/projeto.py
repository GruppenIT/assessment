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
from werkzeug.security import generate_password_hash
import logging

projeto_bp = Blueprint('projeto', __name__, url_prefix='/admin/projetos')

@projeto_bp.route('/')
@login_required
@admin_required
def listar():
    """Lista todos os projetos com filtro opcional por cliente"""
    # Obter filtro de cliente se fornecido
    cliente_id = request.args.get('cliente_id', type=int)
    
    # Query base
    query = Projeto.query.filter_by(ativo=True)
    
    # Aplicar filtro por cliente se selecionado
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    projetos = query.order_by(Projeto.data_criacao.desc()).all()
    
    # Obter lista de clientes para o filtro
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    
    projetos_data = []
    for projeto in projetos:
        progresso = projeto.get_progresso_geral()
        projetos_data.append({
            'projeto': projeto,
            'progresso': progresso,
            'concluido': projeto.is_concluido(),
            'respondentes_count': len(projeto.get_respondentes_ativos()),
            'tipos_count': len(projeto.get_tipos_assessment())
        })
    
    return render_template('admin/projetos/listar.html', 
                         projetos_data=projetos_data,
                         clientes=clientes,
                         cliente_selecionado=cliente_id)

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
                
                # Associar tipos de assessment
                for tipo_id in tipos_ids:
                    projeto_assessment = ProjetoAssessment(
                        projeto_id=projeto.id,
                        tipo_assessment_id=int(tipo_id)
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
    
    # Progresso por tipo de assessment
    progressos_por_tipo = {}
    for tipo in tipos_assessment:
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        
        total_perguntas = Pergunta.query.join(Dominio).filter(
            Dominio.tipo_assessment_id == tipo.id,
            Dominio.ativo == True,
            Pergunta.ativo == True
        ).count()
        
        total_respostas = 0
        for respondente in respondentes:
            from models.resposta import Resposta
            respostas_count = Resposta.query.filter_by(
                respondente_id=respondente.id,
                projeto_id=projeto.id
            ).join(Pergunta).join(Dominio).filter(
                Dominio.tipo_assessment_id == tipo.id
            ).count()
            total_respostas += respostas_count
        
        total_esperado = total_perguntas * len(respondentes)
        progresso_tipo = round((total_respostas / total_esperado * 100) if total_esperado > 0 else 0, 1)
        
        progressos_por_tipo[tipo.id] = {
            'tipo': tipo,
            'progresso': progresso_tipo,
            'respostas': total_respostas,
            'total': total_esperado
        }
    
    return render_template('admin/projetos/detalhar.html',
                         projeto=projeto,
                         progresso=progresso,
                         respondentes=respondentes,
                         tipos_assessment=tipos_assessment,
                         progressos_por_tipo=progressos_por_tipo)

@projeto_bp.route('/<int:projeto_id>/respondentes')
@login_required
@admin_required
def gerenciar_respondentes(projeto_id):
    """Gerencia respondentes do projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    from forms.projeto_forms import AdicionarRespondenteForm
    form = AdicionarRespondenteForm(cliente_id=projeto.cliente_id, projeto_id=projeto.id)
    
    # Respondentes atuais do projeto (objetos ProjetoRespondente)
    projeto_respondentes = ProjetoRespondente.query.filter_by(
        projeto_id=projeto.id, 
        ativo=True
    ).all()
    
    # Extrair os objetos Respondente
    respondentes_projeto = [pr.respondente for pr in projeto_respondentes]
    
    # Respondentes disponíveis do cliente que não estão no projeto
    respondentes_disponiveis = []
    for resp in projeto.cliente.get_respondentes_ativos():
        if resp not in respondentes_projeto:
            respondentes_disponiveis.append(resp)
    
    return render_template('admin/projetos/gerenciar_respondentes.html',
                         projeto=projeto,
                         form=form,
                         respondentes_projeto=respondentes_projeto,
                         respondentes_disponiveis=respondentes_disponiveis)

@projeto_bp.route('/<int:projeto_id>/adicionar-respondente', methods=['POST'])
@login_required
@admin_required
def adicionar_respondente(projeto_id):
    """Adiciona um respondente existente ao projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    from forms.projeto_forms import AdicionarRespondenteForm
    form = AdicionarRespondenteForm(cliente_id=projeto.cliente_id, projeto_id=projeto.id)
    
    if form.validate_on_submit():
        try:
            respondente_id = int(form.respondente_id.data) if form.respondente_id.data else None
            
            if not respondente_id:
                flash('Selecione um respondente válido.', 'danger')
                return redirect(url_for('projeto.gerenciar_respondentes', projeto_id=projeto_id))
            
            # Verificar se já está associado
            associacao_existente = ProjetoRespondente.query.filter_by(
                projeto_id=projeto.id,
                respondente_id=respondente_id
            ).first()
            
            if associacao_existente:
                if not associacao_existente.ativo:
                    associacao_existente.ativo = True
                    db.session.commit()
                    flash('Respondente reativado no projeto!', 'success')
                else:
                    flash('Respondente já está no projeto.', 'info')
            else:
                # Criar nova associação
                projeto_respondente = ProjetoRespondente(
                    projeto_id=projeto.id,
                    respondente_id=respondente_id,
                    ativo=True
                )
                db.session.add(projeto_respondente)
                db.session.commit()
                
                respondente = Respondente.query.get(respondente_id)
                flash(f'Respondente "{respondente.nome}" adicionado ao projeto!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao adicionar respondente: {e}")
            flash('Erro ao adicionar respondente. Tente novamente.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('projeto.gerenciar_respondentes', projeto_id=projeto_id))

@projeto_bp.route('/<int:projeto_id>/associar-respondente/<int:respondente_id>', methods=['POST'])
@login_required
@admin_required
def associar_respondente_existente(projeto_id, respondente_id):
    """Associa um respondente existente ao projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    respondente = Respondente.query.get_or_404(respondente_id)
    
    # Verificar se respondente pertence ao cliente do projeto
    if respondente.cliente_id != projeto.cliente_id:
        flash('Respondente não pertence ao cliente do projeto.', 'danger')
        return redirect(url_for('projeto.gerenciar_respondentes', projeto_id=projeto_id))
    
    # Verificar se já está associado
    associacao_existente = ProjetoRespondente.query.filter_by(
        projeto_id=projeto.id,
        respondente_id=respondente.id
    ).first()
    
    if associacao_existente:
        if not associacao_existente.ativo:
            associacao_existente.ativo = True
            db.session.commit()
            flash(f'Respondente "{respondente.nome}" reativado no projeto!', 'success')
        else:
            flash(f'Respondente "{respondente.nome}" já está no projeto.', 'info')
    else:
        try:
            projeto_respondente = ProjetoRespondente(
                projeto_id=projeto.id,
                respondente_id=respondente.id,
                ativo=True
            )
            db.session.add(projeto_respondente)
            db.session.commit()
            flash(f'Respondente "{respondente.nome}" adicionado ao projeto!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao associar respondente: {e}")
            flash('Erro ao associar respondente. Tente novamente.', 'danger')
    
    return redirect(url_for('projeto.gerenciar_respondentes', projeto_id=projeto_id))

@projeto_bp.route('/<int:projeto_id>/remover-respondente/<int:respondente_id>', methods=['POST'])
@login_required
@admin_required
def remover_respondente(projeto_id, respondente_id):
    """Remove um respondente do projeto"""
    projeto_respondente = ProjetoRespondente.query.filter_by(
        projeto_id=projeto_id,
        respondente_id=respondente_id
    ).first_or_404()
    
    try:
        projeto_respondente.ativo = False
        db.session.commit()
        flash('Respondente removido do projeto.', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao remover respondente: {e}")
        flash('Erro ao remover respondente. Tente novamente.', 'danger')
    
    return redirect(url_for('projeto.gerenciar_respondentes', projeto_id=projeto_id))

@projeto_bp.route('/<int:projeto_id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar(projeto_id):
    """Edita um projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    form = ProjetoForm(obj=projeto)
    
    if form.validate_on_submit():
        try:
            projeto.nome = form.nome.data
            projeto.cliente_id = form.cliente_id.data
            projeto.descricao = form.descricao.data
            
            # Atualizar tipos de assessment
            # Remover associações atuais
            ProjetoAssessment.query.filter_by(projeto_id=projeto.id).delete()
            
            # Adicionar novas associações
            for tipo_id in form.tipos_assessment.data:
                projeto_assessment = ProjetoAssessment(
                    projeto_id=projeto.id,
                    tipo_assessment_id=tipo_id
                )
                db.session.add(projeto_assessment)
            
            db.session.commit()
            flash(f'Projeto "{projeto.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('projeto.detalhar', projeto_id=projeto.id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erro ao editar projeto: {e}")
            flash('Erro ao editar projeto. Tente novamente.', 'danger')
    
    # Pré-selecionar tipos de assessment atuais
    tipos_selecionados = [pa.tipo_assessment_id for pa in projeto.assessments]
    form.tipos_assessment.data = tipos_selecionados
    
    # Criar formulário para novo cliente
    from forms.cliente_forms import NovoClienteForm
    novo_cliente_form = NovoClienteForm()
    
    return render_template('admin/projetos/editar.html', 
                         form=form, 
                         projeto=projeto,
                         novo_cliente_form=novo_cliente_form)

@projeto_bp.route('/<int:projeto_id>/desativar', methods=['POST'])
@login_required
@admin_required
def desativar(projeto_id):
    """Desativa um projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    try:
        projeto.ativo = False
        db.session.commit()
        flash(f'Projeto "{projeto.nome}" desativado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao desativar projeto: {e}")
        flash('Erro ao desativar projeto.', 'danger')
    
    return redirect(url_for('projeto.listar'))

@projeto_bp.route('/<int:projeto_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir(projeto_id):
    """Exclui um projeto permanentemente"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    try:
        nome_projeto = projeto.nome
        
        # Remover todas as associações primeiro
        ProjetoRespondente.query.filter_by(projeto_id=projeto.id).delete()
        ProjetoAssessment.query.filter_by(projeto_id=projeto.id).delete()
        
        # Remover respostas relacionadas (se existirem)
        from models.resposta import Resposta
        Resposta.query.filter_by(projeto_id=projeto.id).delete()
        
        # Remover o projeto
        db.session.delete(projeto)
        db.session.commit()
        
        flash(f'Projeto "{nome_projeto}" excluído permanentemente!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao excluir projeto: {e}")
        flash('Erro ao excluir projeto. Tente novamente.', 'danger')
    
    return redirect(url_for('projeto.listar'))

@projeto_bp.route('/<int:projeto_id>/desativar', methods=['POST'])
@login_required
@admin_required
def desativar(projeto_id):
    """Desativa um projeto"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    try:
        projeto.ativo = False
        db.session.commit()
        flash(f'Projeto "{projeto.nome}" desativado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao desativar projeto: {e}")
        flash('Erro ao desativar projeto. Tente novamente.', 'danger')
    
    return redirect(url_for('projeto.listar'))