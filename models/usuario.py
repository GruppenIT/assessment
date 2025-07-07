from app import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    """Modelo para usuários do sistema (clientes e administradores)"""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, comment='Nome do usuário ou responsável')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='Email usado como login')
    senha_hash = db.Column(db.String(256), nullable=False, comment='Hash da senha')
    tipo = db.Column(db.String(20), nullable=False, default='cliente', comment='Tipo: cliente ou admin')
    
    # Campos específicos para clientes (empresas)
    nome_empresa = db.Column(db.String(200), comment='Nome da empresa (apenas para clientes)')
    
    # Metadados
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação do usuário')
    ativo = db.Column(db.Boolean, default=True, comment='Se o usuário está ativo')
    
    # Relacionamentos
    respostas = db.relationship('Resposta', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Usuario {self.email}>'
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.tipo == 'admin'
    
    def is_cliente(self):
        """Verifica se o usuário é cliente"""
        return self.tipo == 'cliente'
    
    def get_progresso_assessment(self):
        """Calcula o progresso do assessment do cliente"""
        if not self.is_cliente():
            return 0
        
        from models.pergunta import Pergunta
        total_perguntas = Pergunta.query.count()
        
        if total_perguntas == 0:
            return 0
        
        respostas_dadas = len(self.respostas)
        return round((respostas_dadas / total_perguntas) * 100, 1)
    
    def assessment_concluido(self):
        """Verifica se o cliente concluiu o assessment"""
        from models.pergunta import Pergunta
        total_perguntas = Pergunta.query.count()
        respostas_dadas = len(self.respostas)
        return total_perguntas > 0 and respostas_dadas >= total_perguntas
    
    def to_dict(self):
        """Converte o usuário para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo,
            'nome_empresa': self.nome_empresa,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'ativo': self.ativo
        }
