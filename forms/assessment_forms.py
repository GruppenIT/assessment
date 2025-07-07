from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Optional, Length

class RespostaForm(FlaskForm):
    """Formulário para respostas do assessment"""
    pergunta_id = HiddenField('Pergunta ID', validators=[
        DataRequired(message='ID da pergunta é obrigatório')
    ])
    
    nota = IntegerField('Nota', validators=[
        DataRequired(message='Nota é obrigatória'),
        NumberRange(min=0, max=5, message='Nota deve ser entre 0 e 5')
    ])
    
    comentario = TextAreaField('Comentário', validators=[
        Optional(),
        Length(max=1000, message='Comentário deve ter no máximo 1000 caracteres')
    ], render_kw={'placeholder': 'Comentário opcional sobre esta questão', 'rows': 3})
    
    submit = SubmitField('Salvar Resposta')
    
    def __init__(self, *args, **kwargs):
        super(RespostaForm, self).__init__(*args, **kwargs)
        
        # Definir opções de nota
        self.opcoes_nota = [
            (0, 'Não implementado'),
            (1, 'Inicial'),
            (2, 'Em desenvolvimento'),
            (3, 'Definido'),
            (4, 'Gerenciado'),
            (5, 'Otimizado')
        ]
