from datetime import datetime
from app import db

class TipoAssessment(db.Model):
    """Modelo para tipos de assessment (ex: Cibersegurança, Compliance, etc.)"""
    
    __tablename__ = 'tipos_assessment'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, comment='Nome do tipo de assessment')
    versao = db.Column(db.String(10), nullable=False, default='1.0', comment='Versão do assessment')
    descricao = db.Column(db.Text, comment='Descrição do tipo de assessment')
    ordem = db.Column(db.Integer, default=1, comment='Ordem de exibição')
    ativo = db.Column(db.Boolean, default=True, comment='Se o tipo está ativo')
    url_publica = db.Column(db.Boolean, default=False, comment='Se o assessment possui URL pública')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    
    # Relacionamentos
    dominios = db.relationship('Dominio', backref='tipo_assessment', lazy=True, cascade='all, delete-orphan')
    cliente_assessments = db.relationship('ClienteAssessment', backref='tipo_assessment', lazy=True, cascade='all, delete-orphan')
    # projetos = db.relationship('ProjetoAssessment', back_populates='tipo_assessment')  # Será adicionado após criar tabelas
    
    def __repr__(self):
        return f'<TipoAssessment {self.nome} v{self.versao}>'
    
    def get_dominios_ativos(self):
        """Retorna domínios ativos do tipo de assessment"""
        return [d for d in self.dominios if d.ativo]
    
    def contar_dominios(self):
        """Conta o número de domínios ativos no tipo"""
        return len(self.get_dominios_ativos())
    
    def contar_perguntas(self):
        """Conta o número total de perguntas ativas no tipo"""
        total = 0
        for dominio in self.get_dominios_ativos():
            total += dominio.contar_perguntas()
        return total
    
    def to_dict(self):
        """Converte o tipo de assessment para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'versao': self.versao,
            'descricao': self.descricao,
            'ordem': self.ordem,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'total_dominios': self.contar_dominios(),
            'total_perguntas': self.contar_perguntas()
        }