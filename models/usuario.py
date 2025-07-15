from app import db
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    """Modelo para usuários administradores do sistema"""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, comment='Nome do administrador')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='Email usado como login')
    senha_hash = db.Column(db.String(256), nullable=False, comment='Hash da senha')
    tipo = db.Column(db.String(20), nullable=False, default='admin', comment='Tipo: sempre admin')
    
    # Metadados
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação do usuário')
    ativo = db.Column(db.Boolean, default=True, comment='Se o usuário está ativo')
    
    def __repr__(self):
        return f'<Usuario {self.email}>'
    
    def is_admin(self):
        """Verifica se o usuário é administrador"""
        return self.tipo == 'admin'
    
    def is_cliente(self):
        """Verifica se o usuário é cliente (sempre False para Usuario)"""
        return False
    
    def to_dict(self):
        """Converte o usuário para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'tipo': self.tipo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'ativo': self.ativo
        }
