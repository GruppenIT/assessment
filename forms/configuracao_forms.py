from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import ColorInput

class ConfiguracaoForm(FlaskForm):
    """Formulário para configurações do sistema"""
    
    # Cores do sistema
    cor_primaria = StringField('Cor Primária', 
                               validators=[DataRequired(message='Cor primária é obrigatória')],
                               widget=ColorInput(),
                               render_kw={'value': '#0d6efd'})
    
    cor_secundaria = StringField('Cor Secundária',
                                validators=[DataRequired(message='Cor secundária é obrigatória')],
                                widget=ColorInput(),
                                render_kw={'value': '#6c757d'})
    
    cor_sucesso = StringField('Cor de Sucesso',
                             validators=[DataRequired(message='Cor de sucesso é obrigatória')],
                             widget=ColorInput(),
                             render_kw={'value': '#198754'})
    
    cor_perigo = StringField('Cor de Perigo',
                            validators=[DataRequired(message='Cor de perigo é obrigatória')],
                            widget=ColorInput(),
                            render_kw={'value': '#dc3545'})
    
    cor_aviso = StringField('Cor de Aviso',
                           validators=[DataRequired(message='Cor de aviso é obrigatória')],
                           widget=ColorInput(),
                           render_kw={'value': '#ffc107'})
    
    cor_info = StringField('Cor de Informação',
                          validators=[DataRequired(message='Cor de informação é obrigatória')],
                          widget=ColorInput(),
                          render_kw={'value': '#0dcaf0'})
    
    cor_fundo = StringField('Cor de Fundo',
                           validators=[DataRequired(message='Cor de fundo é obrigatória')],
                           widget=ColorInput(),
                           render_kw={'value': '#ffffff'})
    
    cor_texto = StringField('Cor do Texto',
                           validators=[DataRequired(message='Cor do texto é obrigatória')],
                           widget=ColorInput(),
                           render_kw={'value': '#212529'})
    
    # Configurações de aparência
    tema_escuro = BooleanField('Tema Escuro', default=False)
    logo_navbar = BooleanField('Logo na Barra de Navegação', default=True)
    sidebar_fechada = BooleanField('Sidebar Fechada por Padrão', default=False)
    
    # Botões
    submit = SubmitField('Salvar Configurações')
    reset = SubmitField('Restaurar Padrões', render_kw={'class': 'btn btn-outline-warning'})
    
    def __init__(self, *args, **kwargs):
        super(ConfiguracaoForm, self).__init__(*args, **kwargs)

class ConfiguracaoGeralForm(FlaskForm):
    """Formulário para configurações gerais do sistema"""
    
    nome_sistema = StringField('Nome do Sistema',
                              validators=[DataRequired(message='Nome do sistema é obrigatório'),
                                        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')],
                              render_kw={'placeholder': 'Digite o nome do sistema'})
    
    descricao_sistema = TextAreaField('Descrição do Sistema',
                                     validators=[Optional(),
                                               Length(max=500, message='Descrição deve ter no máximo 500 caracteres')],
                                     render_kw={'placeholder': 'Descrição opcional do sistema', 'rows': 3})
    
    email_suporte = StringField('Email de Suporte',
                               validators=[Optional(),
                                         Length(max=120, message='Email deve ter no máximo 120 caracteres')],
                               render_kw={'placeholder': 'Email para suporte técnico'})
    
    telefone_suporte = StringField('Telefone de Suporte',
                                  validators=[Optional(),
                                            Length(max=20, message='Telefone deve ter no máximo 20 caracteres')],
                                  render_kw={'placeholder': 'Telefone para suporte'})
    
    submit = SubmitField('Salvar Configurações Gerais')