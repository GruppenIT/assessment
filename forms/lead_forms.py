from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional

class LeadUpdateForm(FlaskForm):
    """Formulário para atualizar status e dados do lead"""
    
    status = SelectField('Status', 
                        choices=[
                            ('novo', 'Novo'),
                            ('contatado', 'Contatado'),
                            ('qualificado', 'Qualificado'),
                            ('proposta', 'Proposta Enviada'),
                            ('negociacao', 'Em Negociação'),
                            ('ganho', 'Ganho/Convertido'),
                            ('perdido', 'Perdido')
                        ],
                        validators=[DataRequired()])
    
    prioridade = SelectField('Prioridade',
                            choices=[
                                ('baixa', 'Baixa'),
                                ('media', 'Média'),
                                ('alta', 'Alta')
                            ],
                            validators=[DataRequired()])
    
    atribuido_a_id = SelectField('Atribuído a', 
                                 coerce=int,
                                 validators=[Optional()])
    
    comentarios = TextAreaField('Comentários/Observações',
                               validators=[Optional()])
    
    submit = SubmitField('Atualizar Lead')


class LeadComentarioForm(FlaskForm):
    """Formulário para adicionar comentário ao lead"""
    
    comentario = TextAreaField('Adicionar Comentário',
                               validators=[DataRequired(message='O comentário não pode estar vazio')],
                               render_kw={'rows': 4, 'placeholder': 'Digite seu comentário aqui...'})
    
    submit = SubmitField('Adicionar Comentário')


class LeadFiltroForm(FlaskForm):
    """Formulário para filtrar leads no dashboard"""
    
    status = SelectField('Status',
                        choices=[
                            ('', 'Todos'),
                            ('novo', 'Novo'),
                            ('contatado', 'Contatado'),
                            ('qualificado', 'Qualificado'),
                            ('proposta', 'Proposta Enviada'),
                            ('negociacao', 'Em Negociação'),
                            ('ganho', 'Ganho/Convertido'),
                            ('perdido', 'Perdido')
                        ],
                        validators=[Optional()])
    
    prioridade = SelectField('Prioridade',
                            choices=[
                                ('', 'Todas'),
                                ('baixa', 'Baixa'),
                                ('media', 'Média'),
                                ('alta', 'Alta')
                            ],
                            validators=[Optional()])
    
    busca = StringField('Buscar (nome, email ou empresa)',
                       validators=[Optional()],
                       render_kw={'placeholder': 'Digite para buscar...'})
    
    submit = SubmitField('Filtrar')
