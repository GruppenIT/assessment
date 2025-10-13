"""
Formulários para parâmetros do sistema
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange

class ParametroSistemaForm(FlaskForm):
    """Formulário para configurações gerais do sistema"""
    
    # Fuso Horário
    fuso_horario = SelectField(
        'Fuso Horário',
        choices=[
            ('America/Sao_Paulo', 'Brasil - GMT-3 (Brasília)'),
            ('America/Fortaleza', 'Brasil - GMT-3 (Fortaleza)'),
            ('America/Recife', 'Brasil - GMT-3 (Recife)'),
            ('America/Manaus', 'Brasil - GMT-4 (Manaus)'),
            ('America/Porto_Velho', 'Brasil - GMT-4 (Porto Velho)'),
            ('UTC', 'UTC - GMT+0'),
            ('America/New_York', 'EUA - EST (Nova York)'),
            ('Europe/London', 'Reino Unido - GMT (Londres)'),
            ('Europe/Paris', 'França - CET (Paris)'),
        ],
        default='America/Sao_Paulo',
        validators=[DataRequired()]
    )
    
    submit_geral = SubmitField('Salvar Configurações Gerais')

class OpenAIConfigForm(FlaskForm):
    """Formulário para configurações do OpenAI"""
    
    openai_api_key = PasswordField(
        'Chave da API OpenAI',
        validators=[Optional(), Length(min=10, max=200)],
        render_kw={'placeholder': 'sk-...'}
    )
    
    openai_assistant_name = StringField(
        'Nome do Assistant GPT',
        validators=[Optional(), Length(min=2, max=100)],
        render_kw={'placeholder': 'Nome do seu assistant personalizado'}
    )
    
    submit_openai = SubmitField('Salvar Configurações OpenAI')

class AparenciaForm(FlaskForm):
    """Formulário para configurações de aparência"""
    
    cor_primaria = StringField(
        'Cor Primária',
        validators=[DataRequired()],
        render_kw={'type': 'color', 'value': '#0d6efd'}
    )
    
    cor_secundaria = StringField(
        'Cor Secundária', 
        validators=[DataRequired()],
        render_kw={'type': 'color', 'value': '#6c757d'}
    )
    
    cor_fundo = StringField(
        'Cor de Fundo',
        validators=[DataRequired()],
        render_kw={'type': 'color', 'value': '#ffffff'}
    )
    
    cor_texto = StringField(
        'Cor do Texto',
        validators=[DataRequired()],
        render_kw={'type': 'color', 'value': '#212529'}
    )
    
    submit_aparencia = SubmitField('Salvar Aparência')

class SMTPConfigForm(FlaskForm):
    """Formulário para configurações de e-mail SMTP"""
    
    # Servidor SMTP
    smtp_server = StringField(
        'Servidor SMTP',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'gruppen-com-br.mail.protection.outlook.com'}
    )
    
    smtp_port = IntegerField(
        'Porta',
        validators=[Optional(), NumberRange(min=1, max=65535)],
        default=587
    )
    
    smtp_use_tls = BooleanField(
        'Conexão Segura (TLS/SSL)',
        default=True
    )
    
    # Tipo de autenticação
    smtp_auth_type = SelectField(
        'Tipo de Autenticação',
        choices=[
            ('basic', 'Autenticação Básica (usuário/senha)'),
            ('oauth2', 'OAuth2 - Microsoft 365')
        ],
        default='oauth2'
    )
    
    # Autenticação básica
    smtp_username = StringField(
        'Usuário SMTP',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'usuario@dominio.com'}
    )
    
    smtp_password = PasswordField(
        'Senha SMTP',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Deixe em branco para manter a senha atual'}
    )
    
    # OAuth2 Microsoft 365
    smtp_client_id = StringField(
        'Client ID',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Client ID da aplicação Azure AD'}
    )
    
    smtp_client_secret = PasswordField(
        'Client Secret',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Deixe em branco para manter o secret atual'}
    )
    
    smtp_refresh_token = PasswordField(
        'Refresh Token',
        validators=[Optional()],
        render_kw={'placeholder': 'Deixe em branco para manter o token atual', 'rows': 3}
    )
    
    smtp_tenant_id = StringField(
        'Tenant ID (Microsoft)',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Tenant ID do Microsoft 365'}
    )
    
    # Remetente
    smtp_from_email = StringField(
        'E-mail Remetente',
        validators=[Optional(), Email(), Length(max=255)],
        render_kw={'placeholder': 'rodrigo@gruppen.com.br'}
    )
    
    smtp_from_name = StringField(
        'Nome do Remetente',
        validators=[Optional(), Length(max=255)],
        default='Assessments',
        render_kw={'placeholder': 'Assessments'}
    )
    
    submit_smtp = SubmitField('Salvar Configurações')