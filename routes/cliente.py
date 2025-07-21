from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from forms.assessment_forms import RespostaForm
from utils.auth_utils import cliente_required, admin_required

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/criar', methods=['GET', 'POST'])
@login_required
@admin_required
def criar():
    """Cria um novo cliente"""
    from forms.cliente_forms import ClienteForm
    from models.cliente import Cliente
    
    form = ClienteForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            cliente = Cliente(
                nome=form.nome.data,
                razao_social=form.razao_social.data,
                cnpj=form.cnpj.data,
                localidade=form.localidade.data,
                segmento=form.segmento.data,
                ativo=True
            )
            
            # Processar upload de logo se houver
            if form.logo.data:
                from utils.upload_utils import save_uploaded_file
                filename = save_uploaded_file(form.logo.data, 'logos')
                if filename:
                    cliente.logo_path = filename
            
            db.session.add(cliente)
            db.session.commit()
            
            # Registrar criação na auditoria
            from models.auditoria import registrar_criacao
            registrar_criacao(
                entidade='cliente',
                entidade_id=cliente.id,
                entidade_nome=cliente.nome,
                detalhes={
                    'razao_social': cliente.razao_social,
                    'cnpj': cliente.cnpj,
                    'localidade': cliente.localidade,
                    'segmento': cliente.segmento
                }
            )
            
            flash(f'Cliente "{cliente.nome}" criado com sucesso!', 'success')
            return redirect(url_for('admin.clientes'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar cliente. Tente novamente.', 'danger')
    
    return render_template('admin/clientes/criar.html', form=form)

@cliente_bp.route('/dashboard')
@login_required
@cliente_required
def dashboard():
    """Dashboard do cliente"""
    # Buscar dados do cliente do respondente logado
    from models.cliente import Cliente
    cliente = Cliente.query.get(current_user.cliente_id)
    
    # Estatísticas do assessment
    total_perguntas = Pergunta.query.filter_by(ativo=True).count()
    respostas_dadas = Resposta.query.filter_by(usuario_id=current_user.id).count()
    progresso = current_user.get_progresso_assessment()
    assessment_concluido = current_user.assessment_concluido()
    
    # Dados por domínio
    dominios = Dominio.query.filter_by(ativo=True).order_by(Dominio.ordem).all()
    stats_dominios = []
    
    for dominio in dominios:
        perguntas_dominio = [p for p in dominio.perguntas if p.ativo]
        respostas_dominio = Resposta.query.join(Pergunta).filter(
            Pergunta.dominio_id == dominio.id,
            Resposta.usuario_id == current_user.id
        ).count()
        
        media_dominio = dominio.calcular_media_respostas(current_user.id)
        
        stats_dominios.append({
            'dominio': dominio,
            'total_perguntas': len(perguntas_dominio),
            'respostas_dadas': respostas_dominio,
            'progresso': round((respostas_dominio / len(perguntas_dominio)) * 100, 1) if perguntas_dominio else 0,
            'media': media_dominio
        })
    
    return render_template('cliente/dashboard.html',
                         cliente=cliente,
                         total_perguntas=total_perguntas,
                         respostas_dadas=respostas_dadas,
                         progresso=progresso,
                         assessment_concluido=assessment_concluido,
                         stats_dominios=stats_dominios)

@cliente_bp.route('/assessment')
@login_required
@cliente_required
def assessment():
    """Página principal do assessment"""
    dominios = Dominio.query.filter_by(ativo=True).order_by(Dominio.ordem).all()
    return render_template('cliente/assessment.html', dominios=dominios)

@cliente_bp.route('/assessment/dominio/<int:dominio_id>')
@login_required
@cliente_required
def assessment_dominio(dominio_id):
    """Assessment de um domínio específico"""
    dominio = Dominio.query.get_or_404(dominio_id)
    perguntas = Pergunta.query.filter_by(dominio_id=dominio_id, ativo=True).order_by(Pergunta.ordem).all()
    
    # Buscar respostas existentes do usuário
    respostas_existentes = {}
    for pergunta in perguntas:
        resposta = pergunta.get_resposta_usuario(current_user.id)
        if resposta:
            respostas_existentes[pergunta.id] = resposta
    
    return render_template('cliente/assessment_dominio.html',
                         dominio=dominio,
                         perguntas=perguntas,
                         respostas_existentes=respostas_existentes)

@cliente_bp.route('/assessment/salvar', methods=['POST'])
@login_required
@cliente_required
def salvar_resposta():
    """Salva uma resposta do assessment via AJAX"""
    try:
        pergunta_id = request.json.get('pergunta_id')
        nota = request.json.get('nota')
        comentario = request.json.get('comentario', '')
        
        if not pergunta_id or nota is None:
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        # Validar nota
        if not isinstance(nota, int) or nota < 0 or nota > 5:
            return jsonify({'success': False, 'message': 'Nota deve ser entre 0 e 5'}), 400
        
        pergunta = Pergunta.query.get_or_404(pergunta_id)
        
        # Buscar resposta existente ou criar nova
        resposta = Resposta.query.filter_by(
            usuario_id=current_user.id,
            pergunta_id=pergunta_id
        ).first()
        
        if resposta:
            # Atualizar resposta existente
            resposta.nota = nota
            resposta.comentario = comentario
        else:
            # Criar nova resposta
            resposta = Resposta(
                usuario_id=current_user.id,
                pergunta_id=pergunta_id,
                nota=nota,
                comentario=comentario
            )
            db.session.add(resposta)
        
        db.session.commit()
        
        # Calcular novo progresso
        progresso = current_user.get_progresso_assessment()
        
        return jsonify({
            'success': True,
            'message': 'Resposta salva com sucesso!',
            'progresso': progresso
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro ao salvar resposta'}), 500

@cliente_bp.route('/assessment/concluir', methods=['POST'])
@login_required
@cliente_required
def concluir_assessment():
    """Conclui o assessment do cliente"""
    if not current_user.assessment_concluido():
        flash('Você precisa responder todas as perguntas antes de concluir o assessment.', 'warning')
        return redirect(url_for('cliente.assessment'))
    
    flash('Assessment concluído com sucesso! Aguarde o contato de nossa equipe.', 'success')
    return redirect(url_for('cliente.dashboard'))

@cliente_bp.route('/meu-relatorio')
@login_required
@cliente_required
def meu_relatorio():
    """Visualiza o próprio relatório (se assessment concluído)"""
    if not current_user.assessment_concluido():
        flash('Você precisa concluir o assessment antes de visualizar o relatório.', 'warning')
        return redirect(url_for('cliente.assessment'))
    
    return redirect(url_for('relatorio.visualizar', usuario_id=current_user.id))
