from datetime import datetime
from app import db
import secrets

class AssessmentPublico(db.Model):
    """Modelo para armazenar respostas de assessments públicos"""
    
    __tablename__ = 'assessments_publicos'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_assessment_id = db.Column(db.Integer, db.ForeignKey('tipos_assessment.id'), nullable=False, comment='Tipo de assessment')
    token = db.Column(db.String(64), unique=True, nullable=False, comment='Token único para acessar resultado')
    
    # Dados do respondente (opcionais até o final do assessment)
    nome_respondente = db.Column(db.String(200), comment='Nome completo do respondente')
    email_respondente = db.Column(db.String(200), comment='Email do respondente')
    telefone_respondente = db.Column(db.String(20), comment='Telefone do respondente')
    cargo_respondente = db.Column(db.String(100), comment='Cargo do respondente')
    empresa_respondente = db.Column(db.String(200), comment='Nome da empresa')
    
    # Controle
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de início do assessment')
    data_conclusao = db.Column(db.DateTime, comment='Data de conclusão do assessment')
    ip_address = db.Column(db.String(50), comment='IP do respondente')
    grupo = db.Column(db.String(100), comment='Grupo/Campanha do assessment (parâmetro ?group=xyz)')
    
    # Relacionamentos
    respostas = db.relationship('RespostaPublica', backref='assessment_publico', lazy=True, cascade='all, delete-orphan')
    tipo_assessment = db.relationship('TipoAssessment', backref='assessments_publicos', lazy=True)
    
    def __repr__(self):
        return f'<AssessmentPublico {self.id} - {self.nome_respondente}>'
    
    @staticmethod
    def gerar_token():
        """Gera um token único para o assessment"""
        return secrets.token_urlsafe(32)
    
    def calcular_pontuacao_geral(self):
        """Calcula a pontuação geral do assessment (0-100)"""
        if not self.respostas:
            return 0
        
        total_pontos = sum(r.valor for r in self.respostas)
        max_pontos = len(self.respostas) * 5  # Valor máximo é 5
        
        if max_pontos == 0:
            return 0
        
        return round((total_pontos / max_pontos) * 100, 1)
    
    def calcular_pontuacao_dominio(self, dominio_id):
        """Calcula a pontuação de um domínio específico (0-100)"""
        respostas_dominio = [r for r in self.respostas if r.pergunta.dominio_versao_id == dominio_id]
        
        if not respostas_dominio:
            return 0
        
        total_pontos = sum(r.valor for r in respostas_dominio)
        max_pontos = len(respostas_dominio) * 5
        
        if max_pontos == 0:
            return 0
        
        return round((total_pontos / max_pontos) * 100, 1)
    
    def get_dominios_respondidos(self):
        """Retorna lista de domínios que foram respondidos (versão versionada)"""
        dominios_ids = set(r.pergunta.dominio_versao_id for r in self.respostas)
        from models.assessment_version import AssessmentDominio
        return AssessmentDominio.query.filter(AssessmentDominio.id.in_(dominios_ids)).all()
    
    def to_dict(self):
        """Converte o assessment público para dicionário"""
        return {
            'id': self.id,
            'tipo_assessment_id': self.tipo_assessment_id,
            'token': self.token,
            'nome_respondente': self.nome_respondente,
            'email_respondente': self.email_respondente,
            'telefone_respondente': self.telefone_respondente,
            'cargo_respondente': self.cargo_respondente,
            'empresa_respondente': self.empresa_respondente,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_conclusao': self.data_conclusao.isoformat() if self.data_conclusao else None,
            'pontuacao_geral': self.calcular_pontuacao_geral(),
            'grupo': self.grupo
        }


class RespostaPublica(db.Model):
    """Modelo para armazenar respostas individuais de assessments públicos"""
    
    __tablename__ = 'respostas_publicas'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_publico_id = db.Column(db.Integer, db.ForeignKey('assessments_publicos.id'), nullable=False, comment='Assessment público')
    pergunta_id = db.Column(db.Integer, db.ForeignKey('perguntas.id'), nullable=False, comment='Pergunta respondida')
    valor = db.Column(db.Integer, nullable=False, comment='Valor da resposta (0=Não, 3=Parcial, 5=Sim)')
    data_resposta = db.Column(db.DateTime, default=datetime.utcnow, comment='Data da resposta')
    
    # Relacionamentos
    pergunta = db.relationship('Pergunta', backref='respostas_publicas', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('valor IN (0, 3, 5)', name='check_valor_publico'),
        db.UniqueConstraint('assessment_publico_id', 'pergunta_id', name='unique_assessment_pergunta_publica'),
    )
    
    def __repr__(self):
        return f'<RespostaPublica Assessment:{self.assessment_publico_id} Pergunta:{self.pergunta_id} Valor:{self.valor}>'
    
    def get_texto_resposta(self):
        """Retorna o texto descritivo da resposta"""
        textos = {
            0: 'Não',
            3: 'Parcial',
            5: 'Sim'
        }
        return textos.get(self.valor, 'Não definido')
    
    def to_dict(self):
        """Converte a resposta pública para dicionário"""
        return {
            'id': self.id,
            'assessment_publico_id': self.assessment_publico_id,
            'pergunta_id': self.pergunta_id,
            'valor': self.valor,
            'texto_resposta': self.get_texto_resposta(),
            'data_resposta': self.data_resposta.isoformat() if self.data_resposta else None
        }
