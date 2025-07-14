"""
Formulários para gerenciamento de projetos
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import CheckboxInput, ListWidget


class MultiCheckboxField(SelectMultipleField):
    """Campo para múltiplas seleções com checkboxes"""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class ProjetoForm(FlaskForm):
    """Formulário para criação/edição de projetos"""
    nome = StringField('Nome do Projeto', validators=[
        DataRequired(message='Nome do projeto é obrigatório'),
        Length(min=2, max=200, message='Nome deve ter entre 2 e 200 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do projeto'})
    
    cliente_id = SelectField('Cliente', validators=[
        DataRequired(message='Cliente é obrigatório')
    ], coerce=int, choices=[])
    
    tipos_assessment = MultiCheckboxField('Tipos de Assessment', validators=[
        DataRequired(message='Selecione pelo menos um tipo de assessment')
    ], coerce=int, choices=[])
    
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
        
        # Popular tipos de assessment
        from models.tipo_assessment import TipoAssessment
        tipos = TipoAssessment.query.filter_by(ativo=True).order_by(TipoAssessment.ordem).all()
        self.tipos_assessment.choices = [(t.id, t.nome) for t in tipos]


class AdicionarRespondenteForm(FlaskForm):
    """Formulário para adicionar respondente ao projeto"""
    respondente_id = SelectField('Respondente', validators=[
        DataRequired(message='Selecione um respondente')
    ], coerce=int, choices=[])
    
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
            
            self.respondente_id.choices = [(r.id, f"{r.nome} ({r.email})") for r in respondentes]
            
            if not self.respondente_id.choices:
                self.respondente_id.choices = [('', 'Nenhum respondente disponível')]