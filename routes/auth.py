from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models.usuario import Usuario
from models.respondente import Respondente
from forms.auth_forms import LoginForm

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
        email = form.email.data.lower().strip()
        senha = form.senha.data
        
        # Primeiro tentar encontrar um administrador
        usuario_admin = Usuario.query.filter_by(email=email, ativo=True).first()
        
        if usuario_admin and check_password_hash(usuario_admin.senha_hash, senha):
            # Login como administrador
            login_user(usuario_admin, remember=form.lembrar.data)
            session['user_type'] = 'admin'
            flash('Login realizado com sucesso!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('admin.dashboard'))
        
        # Se não encontrou admin, tentar encontrar um respondente
        respondente = Respondente.query.filter_by(email=email, ativo=True).first()
        
        if respondente and check_password_hash(respondente.senha_hash, senha):
            # Login como respondente
            login_user(respondente, remember=form.lembrar.data)
            session['user_type'] = 'respondente'
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
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/auto-login')
def auto_login():
    """Auto-login para desenvolvimento"""
    usuario = Usuario.query.filter_by(email='admin@sistema.com').first()
    if usuario:
        login_user(usuario)
        session['user_type'] = 'admin'
        return redirect(url_for('admin.dashboard'))
    else:
        flash('Usuário admin não encontrado', 'error')
        return redirect(url_for('auth.login'))

@auth_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil do usuário"""
    return render_template('auth/perfil.html', usuario=current_user)
