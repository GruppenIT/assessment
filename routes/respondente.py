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
from forms.respondente_forms import LoginResponenteForm
from app import db

respondente_bp = Blueprint('respondente', __name__)

@respondente_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login específico para respondentes"""
    # Se já está logado como respondente, redirecionar para dashboard
    if current_user.is_authenticated and isinstance(current_user, Respondente):
        return redirect(url_for('respondente.dashboard'))
    
    form = LoginResponenteForm()
    
    if form.validate_on_submit():
        email = form.email.data.strip()
        senha = form.senha.data
        
        print(f"DEBUG: Tentativa de login - Email: '{email}', Senha recebida: {'Sim' if senha else 'Não'}")
        
        respondente = Respondente.query.filter_by(email=email, ativo=True).first()
        
        if respondente:
            print(f"DEBUG: Respondente encontrado: {respondente.nome}")
            print(f"DEBUG: Respondente ativo: {respondente.ativo}")
            
            senha_correta = respondente.check_password(senha)
            print(f"DEBUG: Senha correta: {senha_correta}")
            
            if senha_correta:
                try:
                    resultado_login = login_user(respondente, remember=True)
                    print(f"DEBUG: Resultado login_user: {resultado_login}")
                    
                    session['user_type'] = 'respondente'
                    print(f"DEBUG: Session user_type definido: {session.get('user_type')}")
                    
                    # Atualizar último acesso
                    from datetime import datetime
                    respondente.ultimo_acesso = datetime.utcnow()
                    db.session.commit()
                    
                    flash('Login realizado com sucesso!', 'success')
                    print(f"DEBUG: Redirecionando para dashboard...")
                    return redirect(url_for('respondente.dashboard'))
                    
                except Exception as e:
                    print(f"DEBUG: Erro no login: {str(e)}")
                    flash('Erro interno no sistema de login.', 'danger')
            else:
                flash('Senha inválida.', 'danger')
        else:
            print(f"DEBUG: Respondente não encontrado ou inativo para email: '{email}'")
            flash('Email não encontrado ou usuário inativo.', 'danger')
    else:
        if request.method == 'POST':
            print(f"DEBUG: Erro de validação do formulário: {form.errors}")
    
    return render_template('respondente/login.html', form=form)

@respondente_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard do respondente"""
    print(f"DEBUG: Acessando dashboard - current_user: {current_user}")
    print(f"DEBUG: Tipo do current_user: {type(current_user)}")
    print(f"DEBUG: É Respondente? {isinstance(current_user, Respondente)}")
    
    if not isinstance(current_user, Respondente):
        print("DEBUG: Usuário não é respondente, redirecionando para auth.login")
        return redirect(url_for('auth.login'))
    
    try:
        print(f"DEBUG: Cliente do respondente: {current_user.cliente}")
        
        # Obter tipos de assessment do cliente
        tipos_assessment = current_user.cliente.get_tipos_assessment()
        print(f"DEBUG: Tipos de assessment encontrados: {len(tipos_assessment)}")
        
        # Calcular progresso para cada tipo (apenas se houver tipos)
        progressos = {}
        if tipos_assessment:
            for tipo in tipos_assessment:
                print(f"DEBUG: Calculando progresso para tipo: {tipo.nome}")
                progresso = current_user.get_progresso_assessment(tipo.id)
                progressos[tipo.id] = progresso
                print(f"DEBUG: Progresso calculado: {progresso}")
        else:
            print("DEBUG: Nenhum tipo de assessment encontrado - dashboard será exibido com mensagem informativa")
        
        print("DEBUG: Renderizando template dashboard")
        return render_template('respondente/dashboard.html',
                             respondente=current_user,
                             tipos_assessment=tipos_assessment,
                             progressos=progressos)
                             
    except Exception as e:
        print(f"DEBUG: Erro no dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Erro ao carregar dashboard. Entre em contato com o suporte.', 'danger')
        return redirect(url_for('respondente.login'))

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