from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length


class OrientacaoMelhoriaIAForm(FlaskForm):
    """Formulário para orientações de melhoria de textos IA"""
    tipo_texto = HiddenField()
    
    orientacao = TextAreaField(
        'Orientações para Melhoria',
        validators=[
            DataRequired(message='Digite suas orientações para melhoria'),
            Length(min=10, max=1000, message='Orientação deve ter entre 10 e 1000 caracteres')
        ],
        render_kw={
            'rows': 8,
            'placeholder': 'Digite aqui suas orientações para o GPT melhorar o texto...\n\nExemplos:\n- Torne o texto mais técnico\n- Adicione mais detalhes sobre compliance\n- Use linguagem mais comercial\n- Inclua recomendações específicas de ferramentas'
        }
    )
    
    submit = SubmitField('Aplicar Melhorias')