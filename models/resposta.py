from app import db
from datetime import datetime

class Resposta(db.Model):
    """Modelo para respostas dos assessments"""
    
    __tablename__ = 'respostas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, comment='Usuario admin que criou (backward compatibility)')
    respondente_id = db.Column(db.Integer, db.ForeignKey('respondentes.id'), nullable=True, comment='Respondente que respondeu')
    pergunta_id = db.Column(db.Integer, db.ForeignKey('perguntas.id'), nullable=False, comment='Pergunta respondida')
    nota = db.Column(db.Integer, nullable=False, comment='Nota de 0 a 5')
    comentario = db.Column(db.Text, comment='Comentário opcional')
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=True, comment='ID do projeto')
    data_resposta = db.Column(db.DateTime, default=datetime.utcnow, comment='Data da resposta')
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Última atualização')
    
    # Constraint para garantir que a nota está entre 0 e 5
    __table_args__ = (
        db.CheckConstraint('nota >= 0 AND nota <= 5', name='check_nota_range'),
        db.UniqueConstraint('respondente_id', 'pergunta_id', name='unique_respondente_pergunta'),
    )
    
    def __repr__(self):
        return f'<Resposta Usuario:{self.usuario_id} Pergunta:{self.pergunta_id} Nota:{self.nota}>'
    
    def get_texto_nota(self):
        """Retorna o texto descritivo da nota"""
        textos = {
            0: 'Não implementado',
            1: 'Inicial',
            2: 'Em desenvolvimento',
            3: 'Definido',
            4: 'Gerenciado',
            5: 'Otimizado'
        }
        return textos.get(self.nota, 'Não definido')
    
    def get_cor_nota(self):
        """Retorna a cor correspondente à nota para exibição"""
        cores = {
            0: '#dc3545',  # Vermelho
            1: '#fd7e14',  # Laranja
            2: '#ffc107',  # Amarelo
            3: '#28a745',  # Verde claro
            4: '#007bff',  # Azul
            5: '#6f42c1'   # Roxo
        }
        return cores.get(self.nota, '#6c757d')
    
    def to_dict(self):
        """Converte a resposta para dicionário"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'pergunta_id': self.pergunta_id,
            'pergunta_texto': self.pergunta.texto if self.pergunta else None,
            'dominio_nome': self.pergunta.dominio.nome if self.pergunta and self.pergunta.dominio else None,
            'nota': self.nota,
            'texto_nota': self.get_texto_nota(),
            'cor_nota': self.get_cor_nota(),
            'comentario': self.comentario,
            'data_resposta': self.data_resposta.isoformat() if self.data_resposta else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
    
    @staticmethod
    def get_opcoes_nota():
        """Retorna as opções de nota disponíveis"""
        return [
            (0, 'Não implementado'),
            (1, 'Inicial'),
            (2, 'Em desenvolvimento'),
            (3, 'Definido'),
            (4, 'Gerenciado'),
            (5, 'Otimizado')
        ]
