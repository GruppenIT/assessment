"""
Formulários para gerenciamento de projetos
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget


class MultiCheckboxField(SelectMultipleField):
    """Campo para múltiplas seleções com checkboxes"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()
    
    def process_formdata(self, valuelist):
        """Processa dados do formulário para garantir que funcione corretamente"""
        if valuelist:
            try:
                self.data = [self.coerce(x) for x in valuelist if x]
            except (ValueError, TypeError):
                self.data = []
        else:
            self.data = []


class ProjetoForm(FlaskForm):
    """Formulário para criação/edição de projetos"""
    nome = StringField('Nome do Projeto', validators=[
        DataRequired(message='Nome do projeto é obrigatório'),
        Length(min=2, max=70, message='Nome deve ter entre 2 e 70 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do projeto', 'maxlength': '70'})
    
    cliente_id = SelectField('Cliente', validators=[
        DataRequired(message='Cliente é obrigatório')
    ], coerce=int, choices=[])
    
    tipos_assessment = MultiCheckboxField('Tipos de Assessment', coerce=int, choices=[])
    
    descricao = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=1000, message='Descrição deve ter no máximo 1000 caracteres')
    ], render_kw={'placeholder': 'Digite uma descrição para o projeto (opcional)', 'rows': 4})
    
    submit = SubmitField('Salvar Projeto')
    
    def __init__(self, *args, **kwargs):
        super(ProjetoForm, self).__init__(*args, **kwargs)
        
        # Popular clientes
        from models.cliente import Cliente
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        self.cliente_id.choices = [(c.id, c.nome) for c in clientes]
        
        # Popular tipos de assessment (usando sistema novo)
        from models.assessment_version import AssessmentTipo
        tipos = AssessmentTipo.query.filter_by(ativo=True).order_by(AssessmentTipo.nome).all()
        self.tipos_assessment.choices = [(t.id, t.nome) for t in tipos]


class NovoClienteForm(FlaskForm):
    """Formulário simplificado para criar novo cliente durante criação de projeto"""
    nome = StringField('Nome da Empresa', validators=[
        DataRequired(message='Nome da empresa é obrigatório'),
        Length(min=2, max=200, message='Nome deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite o nome da empresa'})
    
    submit = SubmitField('Criar Cliente')


class AdicionarRespondenteForm(FlaskForm):
    """Formulário para adicionar respondente ao projeto"""
    respondente_id = SelectField('Respondente', validators=[
        DataRequired(message='Selecione um respondente')
    ], choices=[])
    
    submit = SubmitField('Adicionar ao Projeto')
    
    def __init__(self, cliente_id=None, projeto_id=None, *args, **kwargs):
        super(AdicionarRespondenteForm, self).__init__(*args, **kwargs)
        
        if cliente_id:
            from models.respondente import Respondente
            from models.projeto import ProjetoRespondente
            
            # Buscar respondentes do cliente que não estão no projeto
            respondentes_no_projeto = []
            if projeto_id:
                respondentes_no_projeto = ProjetoRespondente.query.filter_by(
                    projeto_id=projeto_id,
                    ativo=True
                ).with_entities(ProjetoRespondente.respondente_id).all()
                respondentes_no_projeto = [r[0] for r in respondentes_no_projeto]
            
            respondentes = Respondente.query.filter_by(
                cliente_id=cliente_id,
                ativo=True
            ).filter(~Respondente.id.in_(respondentes_no_projeto)).order_by(Respondente.nome).all()
            
            # Adicionar opção inicial
            choices = [('', 'Selecione um respondente...')]
            choices.extend([(r.id, f"{r.nome} ({r.email})") for r in respondentes])
            
            if len(choices) == 1:  # Só tem a opção inicial
                choices = [('', 'Nenhum respondente disponível')]
            
            self.respondente_id.choices = choices


class AvaliadorForm(FlaskForm):
    """Formulário para editar dados do avaliador responsável pelo projeto"""
    nome_avaliador = StringField('Nome do Avaliador', validators=[
        DataRequired(message='Nome do avaliador é obrigatório'),
        Length(min=2, max=255, message='Nome deve ter entre 2 e 255 caracteres')
    ], render_kw={'placeholder': 'Digite o nome completo do avaliador'})
    
    email_avaliador = StringField('Email do Avaliador', validators=[
        DataRequired(message='Email do avaliador é obrigatório'),
        Length(max=255, message='Email deve ter no máximo 255 caracteres')
    ], render_kw={'placeholder': 'Digite o email profissional do avaliador', 'type': 'email'})
    
    submit = SubmitField('Salvar Dados do Avaliador')