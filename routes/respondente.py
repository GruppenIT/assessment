from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models.respondente import Respondente
from models.cliente import Cliente
from models.tipo_assessment import TipoAssessment
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from forms.assessment_forms import RespostaForm
from app import db

respondente_bp = Blueprint('respondente', __name__)

@respondente_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login específico para respondentes"""
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        print(f"DEBUG: Tentativa de login - Email: {email}")
        
        respondente = Respondente.query.filter_by(email=email, ativo=True).first()
        
        if respondente:
            print(f"DEBUG: Respondente encontrado: {respondente.nome}")
            print(f"DEBUG: Respondente ativo: {respondente.ativo}")
            
            senha_correta = respondente.check_password(senha)
            print(f"DEBUG: Senha correta: {senha_correta}")
            
            if senha_correta:
                login_user(respondente)
                session['user_type'] = 'respondente'
                
                # Atualizar último acesso
                from datetime import datetime
                respondente.ultimo_acesso = datetime.utcnow()
                db.session.commit()
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('respondente.dashboard'))
            else:
                flash('Senha inválida.', 'danger')
        else:
            print(f"DEBUG: Respondente não encontrado ou inativo para email: {email}")
            flash('Email não encontrado ou usuário inativo.', 'danger')
    
    return render_template('respondente/login.html')

@respondente_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard do respondente"""
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    # Obter tipos de assessment do cliente
    tipos_assessment = current_user.cliente.get_tipos_assessment()
    
    # Calcular progresso para cada tipo
    progressos = {}
    for tipo in tipos_assessment:
        progresso = current_user.get_progresso_assessment(tipo.id)
        progressos[tipo.id] = progresso
    
    return render_template('respondente/dashboard.html',
                         respondente=current_user,
                         tipos_assessment=tipos_assessment,
                         progressos=progressos)

@respondente_bp.route('/assessment/<int:tipo_assessment_id>')
@login_required
def assessment(tipo_assessment_id):
    """Assessment de um tipo específico"""
    if not isinstance(current_user, Respondente):
        return redirect(url_for('auth.login'))
    
    # Verificar se o cliente tem acesso a este tipo
    if not current_user.cliente.tem_acesso_assessment(tipo_assessment_id):
        flash('Acesso negado a este tipo de assessment.', 'danger')
        return redirect(url_for('respondente.dashboard'))
    
    tipo_assessment = TipoAssessment.query.get_or_404(tipo_assessment_id)
    dominios = tipo_assessment.get_dominios_ativos()
    
    # Preparar formulários para cada pergunta
    forms_data = {}
    for dominio in dominios:
        for pergunta in dominio.get_perguntas_ativas():
            resposta_existente = Resposta.query.filter_by(
                respondente_id=current_user.id,
                pergunta_id=pergunta.id
            ).first()
            
            form = RespostaForm()
            form.pergunta_id.data = pergunta.id
            
            if resposta_existente:
                form.nota.data = resposta_existente.nota
                form.comentario.data = resposta_existente.comentario
            
            forms_data[pergunta.id] = {
                'form': form,
                'resposta': resposta_existente
            }
    
    return render_template('respondente/assessment.html',
                         tipo_assessment=tipo_assessment,
                         dominios=dominios,
                         forms_data=forms_data)

@respondente_bp.route('/assessment/salvar', methods=['POST'])
@login_required
def salvar_resposta():
    """Salva uma resposta via AJAX"""
    if not isinstance(current_user, Respondente):
        return {'success': False, 'message': 'Acesso negado'}, 403
    
    try:
        data = request.get_json()
        pergunta_id = data.get('pergunta_id')
        nota = data.get('nota')
        comentario = data.get('comentario', '')
        
        # Validar pergunta
        pergunta = Pergunta.query.get(pergunta_id)
        if not pergunta:
            return {'success': False, 'message': 'Pergunta não encontrada'}, 404
        
        # Verificar se o cliente tem acesso
        if not current_user.cliente.tem_acesso_assessment(pergunta.dominio.tipo_assessment_id):
            return {'success': False, 'message': 'Acesso negado'}, 403
        
        # Buscar resposta existente ou criar nova
        resposta = Resposta.query.filter_by(
            respondente_id=current_user.id,
            pergunta_id=pergunta_id
        ).first()
        
        if resposta:
            resposta.nota = nota
            resposta.comentario = comentario
        else:
            resposta = Resposta(
                respondente_id=current_user.id,
                pergunta_id=pergunta_id,
                nota=nota,
                comentario=comentario
            )
            db.session.add(resposta)
        
        db.session.commit()
        
        # Calcular novo progresso
        progresso = current_user.get_progresso_assessment(pergunta.dominio.tipo_assessment_id)
        
        return {
            'success': True,
            'message': 'Resposta salva com sucesso',
            'progresso': progresso['percentual']
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}, 500

@respondente_bp.route('/logout')
@login_required
def logout():
    """Logout do respondente"""
    logout_user()
    session.pop('user_type', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('respondente.login'))