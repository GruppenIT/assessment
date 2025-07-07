from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    """Decorator para rotas que requerem acesso de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Acesso negado. Você precisa ser administrador para acessar esta página.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function

def cliente_required(f):
    """Decorator para rotas que requerem acesso de cliente"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_cliente():
            flash('Acesso negado. Esta área é restrita para clientes.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_or_owner_required(f):
    """Decorator para rotas que requerem ser admin ou dono do recurso"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Se for admin, pode acessar qualquer coisa
        if current_user.is_admin():
            return f(*args, **kwargs)
        
        # Se for cliente, só pode acessar seus próprios dados
        usuario_id = kwargs.get('usuario_id')
        if usuario_id and current_user.id == usuario_id:
            return f(*args, **kwargs)
        
        flash('Acesso negado. Você só pode acessar seus próprios dados.', 'danger')
        abort(403)
    
    return decorated_function

def check_password_strength(password):
    """Verifica a força da senha"""
    errors = []
    
    if len(password) < 6:
        errors.append('A senha deve ter pelo menos 6 caracteres')
    
    if not any(c.isalpha() for c in password):
        errors.append('A senha deve conter pelo menos uma letra')
    
    if not any(c.isdigit() for c in password):
        errors.append('A senha deve conter pelo menos um número')
    
    return errors
