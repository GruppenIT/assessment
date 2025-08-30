"""
Utilitários para autenticação de dois fatores
"""

from flask import session, request, redirect, url_for, flash
from flask_login import current_user
from models.two_factor import TwoFactor
from functools import wraps

def require_2fa_setup(f):
    """
    Decorator que força configuração de 2FA no primeiro login
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Verificar se é respondente e se 2FA está configurado
        if hasattr(current_user, 'cliente_id') and current_user.cliente_id:
            # É respondente
            config = TwoFactor.get_or_create_for_user(respondente_id=current_user.id)
            if not config.is_active:
                return redirect(url_for('auth.setup_2fa'))
        
        # Verificar se passou pela verificação 2FA nesta sessão
        if not session.get('2fa_verified', False):
            return redirect(url_for('auth.verify_2fa'))
        
        return f(*args, **kwargs)
    
    return decorated_function

def check_2fa_required():
    """
    Verifica se usuário precisa configurar ou verificar 2FA
    """
    if not current_user.is_authenticated:
        return None
    
    # Para respondentes, 2FA é obrigatório
    if hasattr(current_user, 'cliente_id') and current_user.cliente_id:
        config = TwoFactor.get_or_create_for_user(respondente_id=current_user.id)
        if not config.is_active:
            return 'setup'  # Precisa configurar
        elif not session.get('2fa_verified', False):
            return 'verify'  # Precisa verificar
    
    # Para admins, 2FA é opcional mas se estiver ativo, precisa verificar
    elif hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
        config = TwoFactor.query.filter_by(usuario_id=current_user.id, is_active=True).first()
        if config and not session.get('2fa_verified', False):
            return 'verify'  # Precisa verificar
    
    return None  # Não precisa de 2FA ou já verificado

def mark_2fa_verified():
    """Marca 2FA como verificado na sessão"""
    session['2fa_verified'] = True
    session['2fa_verified_at'] = request.remote_addr

def clear_2fa_session():
    """Limpa verificação 2FA da sessão"""
    session.pop('2fa_verified', None)
    session.pop('2fa_verified_at', None)

def get_user_2fa_config(user):
    """Obtém configuração 2FA do usuário"""
    if hasattr(user, 'cliente_id') and user.cliente_id:
        # Respondente
        return TwoFactor.get_or_create_for_user(respondente_id=user.id)
    elif hasattr(user, 'tipo') and user.tipo == 'admin':
        # Admin
        return TwoFactor.get_or_create_for_user(usuario_id=user.id)
    
    return None

def is_2fa_enabled_for_user(user):
    """Verifica se 2FA está ativo para o usuário"""
    if hasattr(user, 'cliente_id') and user.cliente_id:
        return TwoFactor.is_enabled_for_user(respondente_id=user.id)
    elif hasattr(user, 'tipo') and user.tipo == 'admin':
        return TwoFactor.is_enabled_for_user(usuario_id=user.id)
    
    return False

def reset_user_2fa(user):
    """Reseta 2FA do usuário (para uso administrativo)"""
    config = get_user_2fa_config(user)
    if config:
        config.reset()
        from app import db
        db.session.commit()
        return True
    return False