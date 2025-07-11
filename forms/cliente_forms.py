from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, Optional, Email
from wtforms.widgets import TextArea

class ClienteForm(FlaskForm):
    """Formulário para cadastro/edição de clientes"""
    nome = StringField('Nome Fantasia', validators=[
        DataRequired(message='Nome fantasia é obrigatório'),
        Length(min=2, max=200, message='Nome deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite o nome fantasia da empresa'})
    
    razao_social = StringField('Razão Social', validators=[
        DataRequired(message='Razão social é obrigatória'),
        Length(min=2, max=200, message='Razão social deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite a razão social da empresa'})
    
    cnpj = StringField('CNPJ', validators=[
        Optional(),
        Length(max=18, message='CNPJ deve ter no máximo 18 caracteres')
    ], render_kw={'placeholder': 'Digite o CNPJ (opcional)', 'data-mask': '00.000.000/0000-00'})
    
    localidade = StringField('Localidade', validators=[
        Optional(),
        Length(max=100, message='Localidade deve ter no máximo 100 caracteres')
    ], render_kw={'placeholder': 'Cidade/Estado'})
    
    segmento = StringField('Segmento', validators=[
        Optional(),
        Length(max=100, message='Segmento deve ter no máximo 100 caracteres')
    ], render_kw={'placeholder': 'Segmento de negócio'})
    
    logo = FileField('Logo da Empresa', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Apenas imagens PNG, JPG ou GIF são permitidas')
    ])
    
    submit = SubmitField('Salvar Cliente')

class ResponenteForm(FlaskForm):
    """Formulário para cadastro/edição de respondentes"""
    nome = StringField('Nome do Respondente', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do respondente'})
    
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Digite um email válido'),
        Length(max=120, message='Email deve ter no máximo 120 caracteres')
    ], render_kw={'placeholder': 'Digite o email'})
    
    senha = PasswordField('Senha', validators=[
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Digite uma senha (deixe vazio para manter atual)'})
    
    cargo = StringField('Cargo', validators=[
        Optional(),
        Length(max=100, message='Cargo deve ter no máximo 100 caracteres')
    ], render_kw={'placeholder': 'Cargo do respondente'})
    
    setor = StringField('Setor', validators=[
        Optional(),
        Length(max=100, message='Setor deve ter no máximo 100 caracteres')
    ], render_kw={'placeholder': 'Setor/departamento'})
    
    ativo = BooleanField('Ativo', default=True)
    
    submit = SubmitField('Salvar Respondente')

class TipoAssessmentForm(FlaskForm):
    """Formulário para cadastro/edição de tipos de assessment"""
    nome = StringField('Nome do Tipo', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do tipo de assessment'})
    
    descricao = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=500, message='Descrição deve ter no máximo 500 caracteres')
    ], render_kw={'placeholder': 'Digite uma descrição (opcional)', 'rows': 3})
    
    ordem = StringField('Ordem', validators=[
        DataRequired(message='Ordem é obrigatória')
    ], default='1', render_kw={'placeholder': 'Ordem de exibição', 'type': 'number', 'min': '1'})
    
    submit = SubmitField('Salvar Tipo')

class ImportacaoCSVForm(FlaskForm):
    """Formulário para importação de dados via CSV"""
    arquivo_csv = FileField('Arquivo CSV', validators=[
        DataRequired(message='Selecione um arquivo CSV'),
        FileAllowed(['csv'], 'Apenas arquivos CSV são permitidos')
    ])
    
    tipo_assessment_id = SelectField('Tipo de Assessment', validators=[
        DataRequired(message='Selecione um tipo de assessment')
    ], coerce=int, choices=[])
    
    submit = SubmitField('Importar Dados')
    
    def __init__(self, *args, **kwargs):
        super(ImportacaoCSVForm, self).__init__(*args, **kwargs)
        from models.tipo_assessment import TipoAssessment
        self.tipo_assessment_id.choices = [
            (ta.id, ta.nome) for ta in TipoAssessment.query.filter_by(ativo=True).order_by(TipoAssessment.nome)
        ]

class ClienteAssessmentForm(FlaskForm):
    """Formulário para associar cliente a tipos de assessment"""
    tipos_assessment = SelectField('Tipos de Assessment', validators=[
        DataRequired(message='Selecione pelo menos um tipo')
    ], coerce=int, choices=[])
    
    submit = SubmitField('Associar')
    
    def __init__(self, *args, **kwargs):
        super(ClienteAssessmentForm, self).__init__(*args, **kwargs)
        from models.tipo_assessment import TipoAssessment
        self.tipos_assessment.choices = [
            (ta.id, ta.nome) for ta in TipoAssessment.query.filter_by(ativo=True).order_by(TipoAssessment.nome)
        ]