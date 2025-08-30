from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class TrocaSenhaObrigatoriaForm(FlaskForm):
    """Formulário para troca obrigatória de senha"""
    
    nova_senha = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=6, message='Nova senha deve ter no mínimo 6 caracteres')
    ], render_kw={'placeholder': 'Digite a nova senha'})
    
    confirmar_senha = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('nova_senha', message='As senhas devem ser iguais')
    ], render_kw={'placeholder': 'Digite a nova senha novamente'})
    
    submit = SubmitField('Alterar Senha')