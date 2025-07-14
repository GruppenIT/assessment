"""
Formulários específicos para respondentes
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginResponenteForm(FlaskForm):
    """Formulário de login para respondentes"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Digite um email válido')
    ], render_kw={'placeholder': 'Digite seu email', 'class': 'form-control form-control-lg'})
    
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ], render_kw={'placeholder': 'Digite sua senha', 'class': 'form-control form-control-lg'})
    
    submit = SubmitField('Entrar', render_kw={'class': 'btn btn-primary btn-lg w-100'})