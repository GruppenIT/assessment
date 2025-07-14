from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea, Select

class ProjetoForm(FlaskForm):
    """Formulário para cadastro/edição de projetos"""
    nome = StringField('Nome do Projeto', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=200, message='Nome deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do projeto'})
    
    cliente_id = SelectField('Cliente', validators=[
        DataRequired(message='Cliente é obrigatório')
    ], coerce=int, choices=[])
    
    tipos_assessment = SelectMultipleField('Tipos de Assessment', validators=[
        DataRequired(message='Selecione pelo menos um tipo de assessment')
    ], coerce=int, choices=[])
    
    descricao = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=1000, message='Descrição deve ter no máximo 1000 caracteres')
    ], render_kw={'placeholder': 'Digite uma descrição do projeto (opcional)', 'rows': 3})
    
    submit = SubmitField('Salvar Projeto')
    
    def __init__(self, *args, **kwargs):
        super(ProjetoForm, self).__init__(*args, **kwargs)
        
        # Carregar clientes ativos
        from models.cliente import Cliente
        self.cliente_id.choices = [(0, 'Selecione um cliente')] + [
            (c.id, c.nome) for c in Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        ]
        
        # Carregar tipos de assessment ativos
        from models.tipo_assessment import TipoAssessment
        self.tipos_assessment.choices = [
            (t.id, f"{t.nome} v{t.versao}") for t in TipoAssessment.query.filter_by(ativo=True).order_by(TipoAssessment.nome, TipoAssessment.versao).all()
        ]

class NovoClienteForm(FlaskForm):
    """Formulário simplificado para criar cliente durante criação do projeto"""
    nome = StringField('Nome do Cliente', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=200, message='Nome deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do cliente'})
    
    submit = SubmitField('Criar Cliente')

class ProjetoResponenteForm(FlaskForm):
    """Formulário para adicionar respondente ao projeto"""
    nome = StringField('Nome do Respondente', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do respondente'})
    
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Length(max=120, message='Email deve ter no máximo 120 caracteres')
    ], render_kw={'placeholder': 'Digite o email do respondente'})
    
    senha = StringField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Digite uma senha'})
    
    cargo = StringField('Cargo', validators=[
        Optional(),
        Length(max=100, message='Cargo deve ter no máximo 100 caracteres')
    ], render_kw={'placeholder': 'Cargo do respondente'})
    
    setor = StringField('Setor', validators=[
        Optional(),
        Length(max=100, message='Setor deve ter no máximo 100 caracteres')
    ], render_kw={'placeholder': 'Setor/departamento'})
    
    submit = SubmitField('Adicionar Respondente')

class AssessmentCSVForm(FlaskForm):
    """Formulário para importação de assessment via CSV"""
    arquivo_csv = FileField('Arquivo CSV', validators=[
        FileRequired(message='Selecione um arquivo CSV'),
        FileAllowed(['csv'], 'Apenas arquivos CSV são permitidos')
    ])
    
    nome_assessment = StringField('Nome do Assessment', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ], render_kw={'placeholder': 'Nome do tipo de assessment'})
    
    versao = StringField('Versão', validators=[
        DataRequired(message='Versão é obrigatória'),
        Length(min=1, max=10, message='Versão deve ter entre 1 e 10 caracteres')
    ], render_kw={'placeholder': 'Ex: 1.0, 2.1'})
    
    descricao = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=500, message='Descrição deve ter no máximo 500 caracteres')
    ], render_kw={'placeholder': 'Descrição do assessment (opcional)', 'rows': 3})
    
    submit = SubmitField('Importar Assessment')