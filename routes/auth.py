from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models.usuario import Usuario
from models.respondente import Respondente
from forms.auth_forms import LoginForm
from utils.password_utils import safe_check_password_hash, safe_generate_password_hash, normalize_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login unificada - detecta automaticamente se é admin ou respondente"""
    if current_user.is_authenticated:
        # Redirecionar baseado no tipo de usuário
        if hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif hasattr(current_user, 'cliente_id'):
            return redirect(url_for('respondente.dashboard'))
        else:
            return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip() if form.email.data else ""
        senha = normalize_password(form.senha.data) if form.senha.data else ""
        
        # Primeiro tentar encontrar um administrador
        usuario_admin = Usuario.query.filter_by(email=email, ativo=True).first()
        
        if usuario_admin and safe_check_password_hash(usuario_admin.senha_hash, senha):
            # Login como administrador
            login_user(usuario_admin, remember=form.lembrar.data)
            session['user_type'] = 'admin'
            
            # Registrar login na auditoria
            from models.auditoria import registrar_login
            registrar_login(
                usuario_tipo='admin',
                usuario_id=usuario_admin.id,
                usuario_nome=usuario_admin.nome,
                usuario_email=usuario_admin.email,
                ip_address=request.remote_addr
            )
            
            flash('Login realizado com sucesso!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('admin.dashboard'))
        
        # Se não encontrou admin, tentar encontrar um respondente por email ou login
        respondente = Respondente.query.filter(
            ((Respondente.email == email) | (Respondente.login == email)),
            Respondente.ativo == True
        ).first()
        
        if respondente and safe_check_password_hash(respondente.senha_hash, senha):
            # Login como respondente
            from datetime import datetime
            respondente.ultimo_acesso = datetime.now()
            db.session.commit()
            
            login_user(respondente, remember=form.lembrar.data)
            session['user_type'] = 'respondente'
            
            # Registrar login na auditoria
            from models.auditoria import registrar_login
            registrar_login(
                usuario_tipo='respondente',
                usuario_id=respondente.id,
                usuario_nome=respondente.nome,
                usuario_email=respondente.email,
                ip_address=request.remote_addr
            )
            
            flash('Login realizado com sucesso!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('respondente.dashboard'))
        
        # Se não encontrou nenhum usuário válido
        flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html', form=form)



@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    # Registrar logout na auditoria antes de fazer logout
    from models.auditoria import registrar_logout
    
    if current_user.is_authenticated:
        usuario_tipo = 'admin' if hasattr(current_user, 'tipo') and current_user.tipo == 'admin' else 'respondente'
        usuario_nome = getattr(current_user, 'nome', 'Usuário')
        usuario_email = getattr(current_user, 'email', None)
        
        registrar_logout(
            usuario_tipo=usuario_tipo,
            usuario_id=current_user.id,
            usuario_nome=usuario_nome,
            usuario_email=usuario_email
        )
    
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

# Rota de auto-login removida por segurança

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Página de perfil com funcionalidade completa de alteração de senha"""
    try:
        # Processar alteração de senha
        if request.method == 'POST':
            senha_atual = normalize_password(request.form.get('senha_atual', '').strip())
            nova_senha = normalize_password(request.form.get('nova_senha', '').strip())
            confirmar_nova_senha = normalize_password(request.form.get('confirmar_nova_senha', '').strip())
            
            # Validações
            if not senha_atual:
                flash('Senha atual é obrigatória.', 'danger')
            elif not nova_senha:
                flash('Nova senha é obrigatória.', 'danger')
            elif len(nova_senha) < 6:
                flash('Nova senha deve ter pelo menos 6 caracteres.', 'danger')
            elif nova_senha != confirmar_nova_senha:
                flash('Confirmação de senha não confere.', 'danger')
            elif not safe_check_password_hash(current_user.senha_hash, senha_atual):
                flash('Senha atual incorreta.', 'danger')
            else:
                # Alterar senha
                try:
                    current_user.senha_hash = safe_generate_password_hash(nova_senha)
                    db.session.commit()
                    
                    # Registrar na auditoria
                    try:
                        from models.auditoria import registrar_auditoria
                        # Determinar tipo de usuário de forma mais robusta
                        usuario_tipo = 'admin'
                        try:
                            if getattr(current_user, 'cliente_id', None):
                                usuario_tipo = 'respondente'
                            elif getattr(current_user, 'tipo', None) == 'admin':
                                usuario_tipo = 'admin'
                        except:
                            usuario_tipo = 'admin'  # Default
                        
                        registrar_auditoria(
                            acao='senha_alterada',
                            usuario_tipo=usuario_tipo,
                            usuario_id=current_user.id,
                            usuario_nome=current_user.nome,
                            detalhes='Senha alterada pelo próprio usuário na página de perfil',
                            ip_address=request.remote_addr
                        )
                    except:
                        pass  # Continua mesmo se auditoria falhar
                    
                    flash('Senha alterada com sucesso!', 'success')
                    return redirect(url_for('auth.perfil'))
                    
                except Exception as e:
                    db.session.rollback()
                    flash('Erro ao alterar senha. Tente novamente.', 'danger')
        
        return render_template('auth/perfil.html')
        
    except Exception as e:
        # Log do erro e retorno de página de erro amigável
        import traceback
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'user_info': {
                'id': getattr(current_user, 'id', 'N/A'),
                'nome': getattr(current_user, 'nome', 'N/A'),
                'email': getattr(current_user, 'email', 'N/A')
            }
        }
        
        return render_template('auth/perfil_erro.html', error_details=error_details), 500
