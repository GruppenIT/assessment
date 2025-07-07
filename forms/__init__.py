"""
Módulo de formulários do sistema de assessment
"""

from .auth_forms import LoginForm, CadastroForm
from .admin_forms import DominioForm, PerguntaForm, LogoForm
from .assessment_forms import RespostaForm

__all__ = ['LoginForm', 'CadastroForm', 'DominioForm', 'PerguntaForm', 'LogoForm', 'RespostaForm']
