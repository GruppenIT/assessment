from app import db
from datetime import datetime

class Pergunta(db.Model):
    """Modelo para perguntas do assessment"""
    
    __tablename__ = 'perguntas'
    
    id = db.Column(db.Integer, primary_key=True)
    # Manter compatibilidade com domínios antigos
    dominio_id = db.Column(db.Integer, db.ForeignKey('dominios.id'), nullable=True, comment='Domínio da pergunta (legado)')
    # Nova referência para domínios versionados
    dominio_versao_id = db.Column(db.Integer, db.ForeignKey('assessment_dominios.id'), nullable=True, comment='Domínio versionado')
    texto = db.Column(db.Text, nullable=False, comment='Texto da pergunta')
    descricao = db.Column(db.Text, comment='Descrição detalhada da pergunta')
    referencia = db.Column(db.Text, comment='Referência teórica/conformidade (ex: ISO 27001:2022 A.6.1.2, NIST CSF GV.PR-1)')
    recomendacao = db.Column(db.Text, comment='Recomendação para correção/melhoria do controle')
    light = db.Column(db.Boolean, default=False, comment='Se a pergunta faz parte do questionário light (1=Sim, 0=Não)')
    ordem = db.Column(db.Integer, default=1, comment='Ordem dentro do domínio')
    ativo = db.Column(db.Boolean, default=True, comment='Se a pergunta está ativa')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    
    # Relacionamentos
    respostas = db.relationship('Resposta', backref='pergunta', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Pergunta {self.id}: {self.texto[:50]}...>'
    
    def get_resposta_usuario(self, usuario_id):
        """Busca a resposta de um usuário específico para esta pergunta"""
        from models.resposta import Resposta
        return Resposta.query.filter_by(
            usuario_id=usuario_id,
            pergunta_id=self.id
        ).first()
    
    def calcular_media_respostas(self):
        """Calcula a média das respostas para esta pergunta"""
        if not self.respostas:
            return 0
        
        total = sum(resposta.nota for resposta in self.respostas)
        return round(total / len(self.respostas), 2)
    
    def contar_respostas(self):
        """Conta o número de respostas para esta pergunta"""
        return len(self.respostas)
    
    def to_dict(self):
        """Converte a pergunta para dicionário"""
        return {
            'id': self.id,
            'dominio_id': self.dominio_id,
            'dominio_nome': self.dominio.nome if self.dominio else None,
            'texto': self.texto,
            'descricao': self.descricao,
            'ordem': self.ordem,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'total_respostas': self.contar_respostas(),
            'media_respostas': self.calcular_media_respostas()
        }
