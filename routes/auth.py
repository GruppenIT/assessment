from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models.usuario import Usuario
from forms.auth_forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        if current_user.tipo == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('cliente.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        senha = form.senha.data
        
        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        
        if usuario and check_password_hash(usuario.senha_hash, senha):
            login_user(usuario, remember=form.lembrar.data)
            flash('Login realizado com sucesso!', 'success')
            
            # Redirecionar para a página solicitada ou dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html', form=form)



@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil do usuário"""
    return render_template('auth/perfil.html', usuario=current_user)
