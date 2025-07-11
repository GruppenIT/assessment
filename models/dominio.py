from app import db
from datetime import datetime

class Dominio(db.Model):
    """Modelo para domínios de assessment"""
    
    __tablename__ = 'dominios'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_assessment_id = db.Column(db.Integer, db.ForeignKey('tipos_assessment.id'), nullable=False, comment='Tipo de assessment do domínio')
    nome = db.Column(db.String(100), nullable=False, comment='Nome do domínio')
    descricao = db.Column(db.Text, comment='Descrição do domínio')
    ordem = db.Column(db.Integer, default=1, comment='Ordem de exibição')
    ativo = db.Column(db.Boolean, default=True, comment='Se o domínio está ativo')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    
    __table_args__ = (
        db.UniqueConstraint('tipo_assessment_id', 'nome', name='unique_tipo_dominio_nome'),
    )
    
    # Relacionamentos
    perguntas = db.relationship('Pergunta', backref='dominio', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Dominio {self.nome}>'
    
    def get_perguntas_ativas(self):
        """Retorna perguntas ativas do domínio"""
        return [p for p in self.perguntas if p.ativo]
    
    def calcular_media_respostas(self, usuario_id=None):
        """Calcula a média das respostas para este domínio"""
        from models.resposta import Resposta
        from models.pergunta import Pergunta
        
        query = db.session.query(db.func.avg(Resposta.nota)).join(
            Pergunta
        ).filter(
            Pergunta.dominio_id == self.id
        )
        
        if usuario_id:
            query = query.filter(Resposta.usuario_id == usuario_id)
        
        media = query.scalar()
        return round(media, 2) if media else 0
    
    def contar_perguntas(self):
        """Conta o número de perguntas ativas no domínio"""
        return len(self.get_perguntas_ativas())
    
    def to_dict(self):
        """Converte o domínio para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ordem': self.ordem,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'total_perguntas': self.contar_perguntas()
        }
