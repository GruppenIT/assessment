from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import ColorInput

class ConfiguracaoForm(FlaskForm):
    """Formulário simplificado para configurações do sistema"""
    
    # Cores básicas do sistema
    cor_primaria = StringField('Cor Primária', 
                               validators=[DataRequired(message='Cor primária é obrigatória')],
                               widget=ColorInput(),
                               render_kw={'value': '#0d6efd'})
    
    cor_secundaria = StringField('Cor Secundária',
                                validators=[DataRequired(message='Cor secundária é obrigatória')],
                                widget=ColorInput(),
                                render_kw={'value': '#6c757d'})
    
    cor_fundo = StringField('Cor de Fundo',
                           validators=[DataRequired(message='Cor de fundo é obrigatória')],
                           widget=ColorInput(),
                           render_kw={'value': '#ffffff'})
    
    cor_texto = StringField('Cor do Texto',
                           validators=[DataRequired(message='Cor do texto é obrigatória')],
                           widget=ColorInput(),
                           render_kw={'value': '#212529'})
    
    # Escala de pontuação - Nomes (sem validação obrigatória)
    escala_0_nome = StringField('Nome Nível 0', render_kw={'value': 'Inexistente'})
    escala_1_nome = StringField('Nome Nível 1', render_kw={'value': 'Inicial'})
    escala_2_nome = StringField('Nome Nível 2', render_kw={'value': 'Básico'})
    escala_3_nome = StringField('Nome Nível 3', render_kw={'value': 'Intermediário'})
    escala_4_nome = StringField('Nome Nível 4', render_kw={'value': 'Avançado'})
    escala_5_nome = StringField('Nome Nível 5', render_kw={'value': 'Otimizado'})
    
    # Escala de pontuação - Cores (sem validação obrigatória)
    escala_0_cor = StringField('Cor Nível 0', widget=ColorInput(), render_kw={'value': '#dc3545'})
    escala_1_cor = StringField('Cor Nível 1', widget=ColorInput(), render_kw={'value': '#fd7e14'})
    escala_2_cor = StringField('Cor Nível 2', widget=ColorInput(), render_kw={'value': '#ffc107'})
    escala_3_cor = StringField('Cor Nível 3', widget=ColorInput(), render_kw={'value': '#20c997'})
    escala_4_cor = StringField('Cor Nível 4', widget=ColorInput(), render_kw={'value': '#0dcaf0'})
    escala_5_cor = StringField('Cor Nível 5', widget=ColorInput(), render_kw={'value': '#198754'})
    
    # Botões
    submit = SubmitField('Salvar Configurações')
    reset = SubmitField('Restaurar Padrões', render_kw={'class': 'btn btn-outline-warning'})
    
    def __init__(self, *args, **kwargs):
        super(ConfiguracaoForm, self).__init__(*args, **kwargs)