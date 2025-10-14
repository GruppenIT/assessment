from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField, TelField
from wtforms.validators import DataRequired, Email, Length, Optional

class RespostaPublicaForm(FlaskForm):
    """Formulário para responder perguntas do assessment público"""
    # Os campos serão criados dinamicamente no controller
    submit = SubmitField('Próximo')

class DadosRespondentePubForm(FlaskForm):
    """Formulário para capturar dados do respondente ao final do assessment"""
    
    nome_completo = StringField('Nome Completo', validators=[
        DataRequired(message='Nome completo é obrigatório'),
        Length(min=3, max=200, message='Nome deve ter entre 3 e 200 caracteres')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=200, message='Email muito longo')
    ])
    
    telefone = TelField('Telefone', validators=[
        Optional(),
        Length(max=20, message='Telefone muito longo')
    ])
    
    cargo = StringField('Cargo', validators=[
        Optional(),
        Length(max=100, message='Cargo muito longo')
    ])
    
    empresa = StringField('Empresa', validators=[
        DataRequired(message='Nome da empresa é obrigatório'),
        Length(min=2, max=200, message='Nome da empresa deve ter entre 2 e 200 caracteres')
    ])
    
    submit = SubmitField('Ver Resultado')

class SolicitarResultadoEmailForm(FlaskForm):
    """Formulário para solicitar resultado por email (apenas email)"""
    
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=200, message='Email muito longo')
    ])
    
    submit = SubmitField('Receber por Email')
