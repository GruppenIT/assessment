"""
Módulo de rotas do sistema de assessment
"""

from .auth import auth_bp
from .cliente import cliente_bp
from .admin import admin_bp
from .relatorio import relatorio_bp

__all__ = ['auth_bp', 'cliente_bp', 'admin_bp', 'relatorio_bp']
