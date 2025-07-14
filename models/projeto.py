from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class Projeto(db.Model):
    """Modelo para projetos de assessment"""
    __tablename__ = 'projetos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime)
    ativo = db.Column(db.Boolean, default=True)
    descricao = db.Column(db.Text)
    
    # Relacionamentos
    cliente = relationship('Cliente', backref='projetos')
    respondentes = relationship('ProjetoRespondente', backref='projeto', cascade='all, delete-orphan')
    assessments = relationship('ProjetoAssessment', backref='projeto', cascade='all, delete-orphan')
    respostas = relationship('Resposta', backref='projeto')
    
    def __repr__(self):
        return f'<Projeto {self.nome}>'
    
    def get_progresso_geral(self):
        """Calcula o progresso geral do projeto"""
        total_perguntas = 0
        total_respostas = 0
        
        for projeto_assessment in self.assessments:
            assessment = projeto_assessment.tipo_assessment
            perguntas_count = sum(len(dominio.perguntas) for dominio in assessment.dominios if dominio.ativo)
            respondentes_count = len([r for r in self.respondentes if r.ativo])
            
            total_perguntas += perguntas_count * respondentes_count
            
            # Contar respostas existentes
            for respondente_proj in self.respondentes:
                if respondente_proj.ativo:
                    respondente = respondente_proj.respondente
                    respostas_count = len([r for r in respondente.respostas 
                                         if r.projeto_id == self.id and 
                                         r.pergunta.dominio.tipo_assessment_id == assessment.id])
                    total_respostas += respostas_count
        
        if total_perguntas == 0:
            return 0
        
        return round((total_respostas / total_perguntas) * 100, 1)
    
    def is_concluido(self):
        """Verifica se o projeto está concluído"""
        return self.get_progresso_geral() >= 100
    
    def get_respondentes_ativos(self):
        """Retorna lista de respondentes ativos do projeto"""
        return [pr.respondente for pr in self.respondentes if pr.ativo]
    
    def get_tipos_assessment(self):
        """Retorna lista de tipos de assessment do projeto"""
        return [pa.tipo_assessment for pa in self.assessments]
    
    def get_progresso_respondente(self, respondente_id):
        """Calcula o progresso geral de um respondente neste projeto"""
        from models.resposta import Resposta
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        
        total_perguntas = 0
        total_respostas = 0
        
        for assessment in self.assessments:
            tipo = assessment.tipo_assessment
            perguntas = Pergunta.query.join(Dominio).filter(
                Dominio.tipo_assessment_id == tipo.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            # Contar TODAS as respostas do projeto (colaborativo)
            respostas = Resposta.query.filter_by(
                projeto_id=self.id
            ).join(Pergunta).join(Dominio).filter(
                Dominio.tipo_assessment_id == tipo.id
            ).count()
            
            total_perguntas += perguntas
            total_respostas += respostas
        
        return round((total_respostas / total_perguntas * 100) if total_perguntas > 0 else 0, 1)


class ProjetoRespondente(db.Model):
    """Modelo para associação entre projeto e respondentes"""
    __tablename__ = 'projeto_respondentes'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    respondente_id = db.Column(db.Integer, db.ForeignKey('respondentes.id'), nullable=False)
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    respondente = relationship('Respondente', backref='projetos')
    
    __table_args__ = (db.UniqueConstraint('projeto_id', 'respondente_id'),)


class ProjetoAssessment(db.Model):
    """Modelo para associação entre projeto e tipos de assessment"""
    __tablename__ = 'projeto_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    tipo_assessment_id = db.Column(db.Integer, db.ForeignKey('tipos_assessment.id'), nullable=False)
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    tipo_assessment = relationship('TipoAssessment', backref='projetos')
    
    __table_args__ = (db.UniqueConstraint('projeto_id', 'tipo_assessment_id'),)