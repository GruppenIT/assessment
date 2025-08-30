"""
Formulários para troca obrigatória de senha
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class TrocaSenhaObrigatoriaForm(FlaskForm):
    """Formulário para troca obrigatória de senha (sem senha atual)"""
    
    nova_senha = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=6, message='A nova senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Digite sua nova senha'})
    
    confirmar_nova_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação é obrigatória'),
        EqualTo('nova_senha', message='As senhas devem ser iguais')
    ], render_kw={'placeholder': 'Digite a nova senha novamente'})
    
    submit = SubmitField('Alterar Senha')