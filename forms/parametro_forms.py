"""
Formulários para parâmetros do sistema
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

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