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
        """Calcula o progresso geral do projeto (colaborativo)"""
        from models.resposta import Resposta
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        
        total_perguntas = 0
        total_respostas_unicas = 0
        
        for projeto_assessment in self.assessments:
            # Usar sistema novo de versionamento
            if projeto_assessment.versao_assessment_id:
                versao = projeto_assessment.versao_assessment
                
                # Contar total de perguntas desta versão
                from models.assessment_version import AssessmentDominio
                perguntas_count = db.session.query(Pergunta).join(
                    AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
                ).filter(
                    AssessmentDominio.versao_id == versao.id,
                    AssessmentDominio.ativo == True,
                    Pergunta.ativo == True
                ).count()
                total_perguntas += perguntas_count
                
                # Contar perguntas únicas respondidas (colaborativo)
                perguntas_respondidas = db.session.query(Pergunta.id).join(
                    Resposta, Pergunta.id == Resposta.pergunta_id
                ).join(AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id).filter(
                    Resposta.projeto_id == self.id,
                    AssessmentDominio.versao_id == versao.id,
                    AssessmentDominio.ativo == True,
                    Pergunta.ativo == True
                ).distinct().count()
                
                total_respostas_unicas += perguntas_respondidas
        
        if total_perguntas == 0:
            return 0
        
        return round((total_respostas_unicas / total_perguntas) * 100, 1)
    
    def is_concluido(self):
        """Verifica se o projeto está concluído"""
        return self.get_progresso_geral() >= 100
    
    def is_totalmente_finalizado(self):
        """Verifica se TODOS os assessments do projeto foram finalizados manualmente"""
        assessments_ativos = [a for a in self.assessments if a.ativo]
        if not assessments_ativos:
            return False
        
        return all(assessment.finalizado for assessment in assessments_ativos)
    
    def get_assessments_finalizados(self):
        """Retorna quantidade de assessments finalizados vs total"""
        assessments_ativos = [a for a in self.assessments if a.ativo]
        finalizados = sum(1 for a in assessments_ativos if a.finalizado)
        return finalizados, len(assessments_ativos)
    
    def get_respondentes_ativos(self):
        """Retorna lista de respondentes ativos do projeto"""
        return [pr.respondente for pr in self.respondentes if pr.ativo]
    
    def get_tipos_assessment(self):
        """Retorna lista de tipos de assessment do projeto"""
        tipos = []
        for pa in self.assessments:
            if pa.versao_assessment_id:
                tipos.append(pa.versao_assessment.tipo)
        return tipos
    
    def get_progresso_respondente(self, respondente_id):
        """Calcula o progresso individual de um respondente neste projeto"""
        from models.resposta import Resposta
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        
        total_perguntas = 0
        total_respostas = 0
        
        for projeto_assessment in self.assessments:
            # Usar sistema novo de versionamento
            if projeto_assessment.versao_assessment_id:
                versao = projeto_assessment.versao_assessment
                
                # Contar total de perguntas desta versão
                from models.assessment_version import AssessmentDominio
                perguntas = db.session.query(Pergunta).join(
                    AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
                ).filter(
                    AssessmentDominio.versao_id == versao.id,
                    AssessmentDominio.ativo == True,
                    Pergunta.ativo == True
                ).count()
                
                # Contar apenas as respostas DESTE respondente específico
                respostas = Resposta.query.filter_by(
                    projeto_id=self.id,
                    respondente_id=respondente_id
                ).join(Pergunta).join(AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id).filter(
                    AssessmentDominio.versao_id == versao.id
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
    """Modelo para associação entre projeto e versões de assessment"""
    __tablename__ = 'projeto_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'), nullable=False)
    # Manter compatibilidade com tipos antigos
    tipo_assessment_id = db.Column(db.Integer, db.ForeignKey('tipos_assessment.id'), nullable=True)
    # Nova referência para versões
    versao_assessment_id = db.Column(db.Integer, db.ForeignKey('assessment_versoes.id'), nullable=True)
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    finalizado = db.Column(db.Boolean, default=False)  # Campo para controle de finalização manual
    data_finalizacao = db.Column(db.DateTime, nullable=True)  # Data da finalização
    
    # Relacionamentos
    tipo_assessment = relationship('TipoAssessment', backref='projetos')
    # versao_assessment definido em assessment_version.py
    
    def pode_editar(self):
        """Verifica se o assessment ainda pode ser editado"""
        return not self.finalizado
    
    def finalizar(self):
        """Finaliza o assessment"""
        self.finalizado = True
        self.data_finalizacao = datetime.utcnow()
        db.session.commit()
    
    def get_progresso_percentual(self):
        """Calcula o percentual de progresso do assessment"""
        from models.pergunta import Pergunta
        from models.dominio import Dominio
        from models.resposta import Resposta
        from models.assessment_version import AssessmentDominio
        
        if self.versao_assessment_id:
            # Novo sistema de versionamento
            versao = self.versao_assessment
            
            # Total de perguntas da versão
            total_perguntas = db.session.query(Pergunta).join(
                AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
            ).filter(
                AssessmentDominio.versao_id == versao.id,
                AssessmentDominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            # Perguntas respondidas do projeto
            perguntas_respondidas = db.session.query(Pergunta.id).join(
                Resposta, Pergunta.id == Resposta.pergunta_id
            ).join(
                AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
            ).filter(
                Resposta.projeto_id == self.projeto_id,
                AssessmentDominio.versao_id == versao.id,
                AssessmentDominio.ativo == True,
                Pergunta.ativo == True
            ).distinct().count()
            
            return round((perguntas_respondidas / total_perguntas * 100) if total_perguntas > 0 else 0, 1)
        
        elif self.tipo_assessment_id:
            # Sistema antigo
            tipo = self.tipo_assessment
            
            # Total de perguntas do tipo
            total_perguntas = Pergunta.query.join(Dominio).filter(
                Dominio.tipo_assessment_id == tipo.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).count()
            
            # Perguntas respondidas do projeto
            perguntas_respondidas = db.session.query(Pergunta.id).join(
                Resposta, Pergunta.id == Resposta.pergunta_id
            ).join(Dominio).filter(
                Resposta.projeto_id == self.projeto_id,
                Dominio.tipo_assessment_id == tipo.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).distinct().count()
            
            return round((perguntas_respondidas / total_perguntas * 100) if total_perguntas > 0 else 0, 1)
        
        return 0
    
    __table_args__ = (
        db.UniqueConstraint('projeto_id', 'tipo_assessment_id'),
        db.UniqueConstraint('projeto_id', 'versao_assessment_id'),
    )