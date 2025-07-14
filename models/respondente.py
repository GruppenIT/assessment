from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Respondente(UserMixin, db.Model):
    """Modelo para respondentes dos clientes"""
    
    __tablename__ = 'respondentes'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False, comment='Cliente do respondente')
    nome = db.Column(db.String(100), nullable=False, comment='Nome do respondente')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='Email usado como login')
    senha_hash = db.Column(db.String(256), nullable=False, comment='Hash da senha')
    cargo = db.Column(db.String(100), comment='Cargo do respondente')
    setor = db.Column(db.String(100), comment='Setor/departamento')
    ativo = db.Column(db.Boolean, default=True, comment='Se o respondente está ativo')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    ultimo_acesso = db.Column(db.DateTime, comment='Último acesso do respondente')
    data_conclusao = db.Column(db.DateTime, comment='Data de conclusão do assessment')
    
    # Relacionamentos
    respostas = db.relationship('Resposta', backref='respondente', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Respondente {self.nome} - {self.email}>'
    
    def set_password(self, password):
        """Define a senha do respondente"""
        self.senha_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica a senha do respondente"""
        return check_password_hash(self.senha_hash, password)
    
    def get_progresso_assessment(self, tipo_assessment_id):
        """Calcula o progresso do assessment para um tipo específico"""
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        from models.resposta import Resposta
        
        # Contar total de perguntas do tipo de assessment
        total_perguntas = db.session.query(Pergunta).join(Dominio).filter(
            Dominio.tipo_assessment_id == tipo_assessment_id,
            Pergunta.ativo == True,
            Dominio.ativo == True
        ).count()
        
        if total_perguntas == 0:
            return {'percentual': 0, 'respondidas': 0, 'total': 0}
        
        # Contar perguntas respondidas por este respondente
        respondidas = db.session.query(Resposta).join(Pergunta).join(Dominio).filter(
            Resposta.respondente_id == self.id,
            Dominio.tipo_assessment_id == tipo_assessment_id
        ).count()
        
        percentual = round((respondidas / total_perguntas) * 100, 1) if total_perguntas > 0 else 0
        
        return {
            'percentual': percentual,
            'respondidas': respondidas,
            'total': total_perguntas
        }
    
    def assessment_concluido(self, tipo_assessment_id):
        """Verifica se o respondente concluiu o assessment de um tipo específico"""
        progresso = self.get_progresso_assessment(tipo_assessment_id)
        return progresso['percentual'] >= 100
    
    def is_admin(self):
        """Respondentes nunca são admins"""
        return False
    
    def assessment_finalizado(self):
        """Verifica se o respondente finalizou o assessment"""
        return self.data_conclusao is not None
    
    def to_dict(self):
        """Converte o respondente para dicionário"""
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'nome': self.nome,
            'email': self.email,
            'cargo': self.cargo,
            'setor': self.setor,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            'data_conclusao': self.data_conclusao.isoformat() if self.data_conclusao else None
        }