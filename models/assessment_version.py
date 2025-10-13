from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class AssessmentTipo(db.Model):
    """Modelo para tipos de assessment com versionamento"""
    
    __tablename__ = 'assessment_tipos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, comment='Nome do tipo de assessment')
    descricao = db.Column(db.Text, comment='Descrição do tipo de assessment')
    ativo = db.Column(db.Boolean, default=True, comment='Se o tipo está ativo')
    url_publica = db.Column(db.Boolean, default=False, comment='Se o assessment possui URL pública')
    cta_texto = db.Column(db.Text, comment='Texto personalizado do CTA para este tipo de assessment')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    
    # Relacionamentos
    versoes = relationship('AssessmentVersao', backref='tipo', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssessmentTipo {self.nome}>'
    
    def get_versao_ativa(self):
        """Retorna a versão ativa (publicada) deste tipo"""
        return AssessmentVersao.query.filter_by(
            tipo_id=self.id,
            status='publicada'
        ).first()
    
    def get_versao_draft(self):
        """Retorna a versão em draft deste tipo, se existir"""
        return AssessmentVersao.query.filter_by(
            tipo_id=self.id,
            status='draft'
        ).first()
    
    def get_versoes_ordenadas(self):
        """Retorna todas as versões ordenadas por versão (mais recente primeiro)"""
        return AssessmentVersao.query.filter_by(
            tipo_id=self.id
        ).order_by(AssessmentVersao.versao.desc()).all()


class AssessmentVersao(db.Model):
    """Modelo para versões de assessment"""
    
    __tablename__ = 'assessment_versoes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_id = db.Column(db.Integer, db.ForeignKey('assessment_tipos.id'), nullable=False)
    versao = db.Column(db.String(50), nullable=False, comment='Número da versão (ex: 1.0, 1.1, 2.0)')
    status = db.Column(db.String(20), nullable=False, default='draft', comment='Status: draft, publicada, arquivada')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    data_publicacao = db.Column(db.DateTime, comment='Data de publicação')
    data_arquivamento = db.Column(db.DateTime, comment='Data de arquivamento')
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    notas_versao = db.Column(db.Text, comment='Notas sobre mudanças nesta versão')
    
    # Relacionamentos
    dominios = relationship('AssessmentDominio', backref='versao', cascade='all, delete-orphan')
    projetos = relationship('ProjetoAssessment', backref='versao_assessment')
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('tipo_id', 'versao', name='unique_tipo_versao'),
        db.CheckConstraint(status.in_(['draft', 'publicada', 'arquivada']), name='check_status'),
    )
    
    def __repr__(self):
        return f'<AssessmentVersao {self.tipo.nome} v{self.versao} ({self.status})>'
    
    def publicar(self):
        """Publica esta versão e arquiva a versão ativa anterior"""
        if self.status != 'draft':
            raise ValueError("Apenas versões em draft podem ser publicadas")
        
        # Arquivar versão ativa anterior
        versao_ativa = self.tipo.get_versao_ativa()
        if versao_ativa:
            versao_ativa.arquivar()
        
        # Publicar esta versão
        self.status = 'publicada'
        self.data_publicacao = datetime.utcnow()
        db.session.commit()
    
    def arquivar(self):
        """Arquiva esta versão"""
        self.status = 'arquivada'
        self.data_arquivamento = datetime.utcnow()
        db.session.commit()
    
    def get_total_perguntas(self):
        """Retorna o total de perguntas ativas nesta versão"""
        from models.pergunta import Pergunta
        return db.session.query(Pergunta).join(AssessmentDominio).filter(
            AssessmentDominio.versao_id == self.id,
            AssessmentDominio.ativo == True,
            Pergunta.ativo == True
        ).count()
    
    def get_dominios_ativos(self):
        """Retorna domínios ativos desta versão ordenados"""
        return AssessmentDominio.query.filter_by(
            versao_id=self.id,
            ativo=True
        ).order_by(AssessmentDominio.ordem).all()


class AssessmentDominio(db.Model):
    """Modelo para domínios de assessment versionados"""
    
    __tablename__ = 'assessment_dominios'
    
    id = db.Column(db.Integer, primary_key=True)
    versao_id = db.Column(db.Integer, db.ForeignKey('assessment_versoes.id'), nullable=False)
    nome = db.Column(db.String(200), nullable=False, comment='Nome do domínio')
    descricao = db.Column(db.Text, comment='Descrição do domínio')
    ordem = db.Column(db.Integer, nullable=False, default=1, comment='Ordem de exibição')
    ativo = db.Column(db.Boolean, default=True, comment='Se o domínio está ativo')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    
    # Relacionamentos
    perguntas = relationship('Pergunta', backref='dominio_versao', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AssessmentDominio {self.nome} (v{self.versao.versao})>'
    
    def get_perguntas_ativas(self):
        """Retorna perguntas ativas deste domínio ordenadas"""
        from models.pergunta import Pergunta
        return Pergunta.query.filter_by(
            dominio_versao_id=self.id,
            ativo=True
        ).order_by(Pergunta.ordem).all()