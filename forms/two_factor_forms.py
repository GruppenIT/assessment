"""
Formulários para autenticação de dois fatores (2FA)
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
import re

class Setup2FAForm(FlaskForm):
    """Formulário para configuração inicial do 2FA"""
    token = StringField(
        'Código do Autenticador',
        validators=[
            DataRequired(message='Digite o código de 6 dígitos'),
            Length(min=6, max=6, message='O código deve ter exatamente 6 dígitos')
        ],
        render_kw={
            'placeholder': '000000',
            'class': 'form-control text-center',
            'style': 'font-size: 1.5em; letter-spacing: 0.5em;',
            'maxlength': '6',
            'autocomplete': 'off'
        }
    )
    
    submit = SubmitField('Ativar 2FA', render_kw={'class': 'btn btn-primary btn-lg'})
    
    def validate_token(self, field):
        """Validar formato do token"""
        if not re.match(r'^\d{6}$', field.data):
            raise ValidationError('O código deve conter apenas números')

class Verify2FAForm(FlaskForm):
    """Formulário para verificação do código 2FA"""
    token = StringField(
        'Código de Verificação',
        validators=[
            DataRequired(message='Digite o código de verificação'),
            Length(min=6, max=8, message='Código inválido')
        ],
        render_kw={
            'placeholder': '000000',
            'class': 'form-control text-center',
            'style': 'font-size: 1.5em; letter-spacing: 0.5em;',
            'maxlength': '8',
            'autocomplete': 'off'
        }
    )
    
    use_backup = HiddenField(default='false')
    submit = SubmitField('Verificar', render_kw={'class': 'btn btn-primary btn-lg'})
    
    def validate_token(self, field):
        """Validar formato do token"""
        # Aceitar códigos de 6 dígitos (TOTP) ou 8 dígitos (backup)
        if not re.match(r'^\d{6,8}$', field.data):
            raise ValidationError('Código deve conter apenas números (6 ou 8 dígitos)')

class Reset2FAForm(FlaskForm):
    """Formulário para reset do 2FA (requer senha atual)"""
    current_password = PasswordField(
        'Senha Atual',
        validators=[DataRequired(message='Digite sua senha atual')],
        render_kw={
            'class': 'form-control',
            'placeholder': 'Sua senha atual'
        }
    )
    
    submit = SubmitField('Resetar 2FA', render_kw={'class': 'btn btn-warning'})

class Backup2FAForm(FlaskForm):
    """Formulário para usar código de backup"""
    backup_code = StringField(
        'Código de Backup',
        validators=[
            DataRequired(message='Digite o código de backup'),
            Length(min=8, max=8, message='O código de backup deve ter 8 dígitos')
        ],
        render_kw={
            'placeholder': '12345678',
            'class': 'form-control text-center',
            'style': 'font-size: 1.2em; letter-spacing: 0.3em;',
            'maxlength': '8'
        }
    )
    
    submit = SubmitField('Usar Código de Backup', render_kw={'class': 'btn btn-secondary'})
    
    def validate_backup_code(self, field):
        """Validar formato do código de backup"""
        if not re.match(r'^\d{8}$', field.data):
            raise ValidationError('O código de backup deve conter apenas 8 números')