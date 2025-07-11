from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class DominioForm(FlaskForm):
    """Formulário para cadastro/edição de domínios"""
    tipo_assessment_id = SelectField('Tipo de Assessment', validators=[
        DataRequired(message='Tipo de assessment é obrigatório')
    ], coerce=int, choices=[])
    
    nome = StringField('Nome do Domínio', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ], render_kw={'placeholder': 'Digite o nome do domínio'})
    
    descricao = TextAreaField('Descrição', validators=[
        Optional(),
        Length(max=500, message='Descrição deve ter no máximo 500 caracteres')
    ], render_kw={'placeholder': 'Digite uma descrição (opcional)', 'rows': 3})
    
    ordem = IntegerField('Ordem', validators=[
        DataRequired(message='Ordem é obrigatória'),
        NumberRange(min=1, message='Ordem deve ser maior que 0')
    ], default=1, render_kw={'placeholder': 'Ordem de exibição'})
    
    submit = SubmitField('Salvar Domínio')
    
    def __init__(self, *args, **kwargs):
        super(DominioForm, self).__init__(*args, **kwargs)
        from models.tipo_assessment import TipoAssessment
        self.tipo_assessment_id.choices = [
            (ta.id, ta.nome) for ta in TipoAssessment.query.filter_by(ativo=True).order_by(TipoAssessment.nome)
        ]

class PerguntaForm(FlaskForm):
    """Formulário para cadastro/edição de perguntas"""
    dominio_id = SelectField('Domínio', validators=[
        DataRequired(message='Domínio é obrigatório')
    ], coerce=int, choices=[])
    
    texto = TextAreaField('Texto da Pergunta', validators=[
        DataRequired(message='Texto da pergunta é obrigatório'),
        Length(min=10, max=1000, message='Texto deve ter entre 10 e 1000 caracteres')
    ], render_kw={'placeholder': 'Digite o texto da pergunta', 'rows': 3})
    
    descricao = TextAreaField('Descrição Detalhada', validators=[
        Optional(),
        Length(max=1000, message='Descrição deve ter no máximo 1000 caracteres')
    ], render_kw={'placeholder': 'Digite uma descrição detalhada (opcional)', 'rows': 4})
    
    ordem = IntegerField('Ordem', validators=[
        DataRequired(message='Ordem é obrigatória'),
        NumberRange(min=1, message='Ordem deve ser maior que 0')
    ], default=1, render_kw={'placeholder': 'Ordem dentro do domínio'})
    
    submit = SubmitField('Salvar Pergunta')
    
    def __init__(self, tipo_assessment_id=None, *args, **kwargs):
        super(PerguntaForm, self).__init__(*args, **kwargs)
        from models.dominio import Dominio
        
        query = Dominio.query.filter_by(ativo=True)
        if tipo_assessment_id:
            query = query.filter_by(tipo_assessment_id=tipo_assessment_id)
        
        self.dominio_id.choices = [
            (d.id, f"{d.tipo_assessment.nome} - {d.nome}") for d in query.order_by(Dominio.nome)
        ]

class LogoForm(FlaskForm):
    """Formulário para upload do logo"""
    logo = FileField('Logo da Empresa', validators=[
        FileRequired(message='Selecione um arquivo'),
        FileAllowed(['png', 'jpg', 'jpeg', 'gif'], 'Apenas imagens PNG, JPG ou GIF são permitidas')
    ])
    
    submit = SubmitField('Atualizar Logo')
