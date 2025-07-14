from datetime import datetime
from app import db

class Cliente(db.Model):
    """Modelo para clientes do sistema"""
    
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, comment='Nome fantasia da empresa')
    razao_social = db.Column(db.String(200), nullable=False, comment='Razão social da empresa')
    cnpj = db.Column(db.String(18), comment='CNPJ da empresa')
    localidade = db.Column(db.String(100), comment='Cidade/Estado do cliente')
    segmento = db.Column(db.String(100), comment='Segmento de negócio')
    logo_path = db.Column(db.String(255), comment='Caminho do logo da empresa')
    ativo = db.Column(db.Boolean, default=True, comment='Se o cliente está ativo')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    
    # Relacionamentos
    respondentes = db.relationship('Respondente', backref='cliente', lazy=True, cascade='all, delete-orphan')
    cliente_assessments = db.relationship('ClienteAssessment', backref='cliente', lazy=True, cascade='all, delete-orphan')
    # projetos = db.relationship('Projeto', back_populates='cliente')  # Será adicionado após criar tabelas
    
    def __repr__(self):
        return f'<Cliente {self.nome}>'
    
    def get_respondentes_ativos(self):
        """Retorna respondentes ativos do cliente"""
        return [r for r in self.respondentes if r.ativo]
    
    def contar_respondentes(self):
        """Conta o número de respondentes ativos"""
        return len(self.get_respondentes_ativos())
    
    def get_tipos_assessment(self):
        """Retorna os tipos de assessment associados ao cliente"""
        return [ca.tipo_assessment for ca in self.cliente_assessments if ca.ativo]
    
    def tem_acesso_assessment(self, tipo_assessment_id):
        """Verifica se o cliente tem acesso a um tipo de assessment"""
        return any(ca.tipo_assessment_id == tipo_assessment_id and ca.ativo 
                  for ca in self.cliente_assessments)
    
    def tem_respondente_finalizado(self):
        """Verifica se o cliente tem pelo menos um respondente que finalizou o assessment"""
        return any(r.data_conclusao is not None for r in self.get_respondentes_ativos())
    
    def to_dict(self):
        """Converte o cliente para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'razao_social': self.razao_social,
            'cnpj': self.cnpj,
            'localidade': self.localidade,
            'segmento': self.segmento,
            'logo_path': self.logo_path,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'total_respondentes': self.contar_respondentes(),
            'tipos_assessment': [ta.to_dict() for ta in self.get_tipos_assessment()]
        }

class ClienteAssessment(db.Model):
    """Tabela de associação entre clientes e tipos de assessment"""
    
    __tablename__ = 'cliente_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    tipo_assessment_id = db.Column(db.Integer, db.ForeignKey('tipos_assessment.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True, comment='Se a associação está ativa')
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data da associação')
    
    __table_args__ = (
        db.UniqueConstraint('cliente_id', 'tipo_assessment_id', name='unique_cliente_tipo_assessment'),
    )
    
    def __repr__(self):
        return f'<ClienteAssessment {self.cliente_id}-{self.tipo_assessment_id}>'