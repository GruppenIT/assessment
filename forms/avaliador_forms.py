from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, EmailField, HiddenField
from wtforms.validators import DataRequired, Optional, Email, Length


class EditarAvaliadorForm(FlaskForm):
    """Formulário para editar dados do avaliador do projeto"""
    nome_avaliador = StringField(
        'Nome do Avaliador',
        validators=[DataRequired(message='Nome do avaliador é obrigatório'),
                    Length(min=2, max=255, message='Nome deve ter entre 2 e 255 caracteres')],
        description='Nome completo do consultor responsável'
    )
    
    email_avaliador = EmailField(
        'Email do Avaliador',
        validators=[DataRequired(message='Email do avaliador é obrigatório'),
                    Email(message='Email inválido'),
                    Length(max=255, message='Email deve ter no máximo 255 caracteres')],
        description='Email profissional que aparecerá na assinatura do relatório'
    )
    
    submit = SubmitField('Salvar Dados do Avaliador')


class EditarTextoIAForm(FlaskForm):
    """Formulário para editar textos gerados por IA"""
    tipo_texto = HiddenField()
    
    texto_ia = TextAreaField(
        'Texto',
        validators=[DataRequired(message='Texto é obrigatório')],
        render_kw={'rows': 15, 'class': 'form-control'}
    )
    
    submit = SubmitField('Salvar Texto')


class LiberarClienteForm(FlaskForm):
    """Formulário para confirmar liberação do projeto para o cliente"""
    confirmacao = HiddenField(default='sim')
    submit = SubmitField('Confirmar Liberação')