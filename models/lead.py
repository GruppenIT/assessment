from datetime import datetime
from app import db

class Lead(db.Model):
    """Modelo para gerenciar leads gerados por assessments públicos"""
    
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    assessment_publico_id = db.Column(db.Integer, db.ForeignKey('assessments_publicos.id'), nullable=False, unique=True, comment='Assessment público que gerou o lead')
    
    # Dados do lead (copiados do assessment público para facilitar queries)
    nome = db.Column(db.String(200), comment='Nome do lead (opcional)')
    email = db.Column(db.String(200), nullable=False, comment='Email do lead (obrigatório)')
    telefone = db.Column(db.String(20), comment='Telefone do lead (opcional)')
    cargo = db.Column(db.String(100), comment='Cargo do lead (opcional)')
    empresa = db.Column(db.String(200), comment='Empresa do lead (opcional)')
    
    # Dados do assessment
    tipo_assessment_nome = db.Column(db.String(200), comment='Nome do tipo de assessment')
    pontuacao_geral = db.Column(db.Float, comment='Pontuação geral obtida (0-100)')
    pontuacoes_dominios = db.Column(db.JSON, comment='Pontuações por domínio em JSON')
    
    # Gestão do lead
    status = db.Column(db.String(50), default='novo', nullable=False, 
                      comment='Status: novo, contatado, qualificado, proposta, ganho, perdido')
    prioridade = db.Column(db.String(20), default='media', 
                          comment='Prioridade: baixa, media, alta')
    
    # Comentários e notas
    comentarios = db.Column(db.Text, comment='Comentários e observações do admin')
    
    # Controle
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='Data de criação do lead')
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Data da última atualização')
    atribuido_a_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), comment='Usuário responsável pelo lead')
    
    # Relacionamentos
    assessment_publico = db.relationship('AssessmentPublico', backref='lead', lazy=True, uselist=False)
    atribuido_a = db.relationship('Usuario', backref='leads', lazy=True)
    
    # Histórico de interações
    historico = db.relationship('LeadHistorico', backref='lead', lazy=True, cascade='all, delete-orphan', order_by='LeadHistorico.data_registro.desc()')
    
    def __repr__(self):
        nome_display = self.nome or self.email
        empresa_display = f' ({self.empresa})' if self.empresa else ''
        return f'<Lead {self.id} - {nome_display}{empresa_display}>'
    
    @staticmethod
    def criar_de_assessment_publico(assessment_publico):
        """Cria um lead a partir de um assessment público"""
        from models.tipo_assessment import TipoAssessment
        
        # Calcular pontuações
        pontuacao_geral = assessment_publico.calcular_pontuacao_geral()
        
        # Calcular pontuações por domínio
        dominios = assessment_publico.get_dominios_respondidos()
        pontuacoes_dominios = {}
        
        for dominio in dominios:
            pontuacao = assessment_publico.calcular_pontuacao_dominio(dominio.id)
            pontuacoes_dominios[dominio.nome] = round(pontuacao, 1)
        
        # Buscar nome do tipo de assessment de forma robusta
        tipo_assessment_nome = "Assessment Público"
        if assessment_publico.tipo_assessment_id:
            tipo = TipoAssessment.query.get(assessment_publico.tipo_assessment_id)
            if tipo:
                tipo_assessment_nome = tipo.nome
        
        # Validar que pelo menos o email existe
        if not assessment_publico.email_respondente:
            raise ValueError("Email do respondente é obrigatório para criar lead")
        
        # Criar lead (campos opcionais podem ser None)
        lead = Lead(
            assessment_publico_id=assessment_publico.id,
            nome=assessment_publico.nome_respondente or None,
            email=assessment_publico.email_respondente,
            telefone=assessment_publico.telefone_respondente or None,
            cargo=assessment_publico.cargo_respondente or None,
            empresa=assessment_publico.empresa_respondente or None,
            tipo_assessment_nome=tipo_assessment_nome,
            pontuacao_geral=pontuacao_geral,
            pontuacoes_dominios=pontuacoes_dominios,
            status='novo'
        )
        
        return lead
    
    def adicionar_historico(self, acao, usuario_id=None, detalhes=None):
        """Adiciona uma entrada ao histórico do lead"""
        historico_entry = LeadHistorico(
            lead_id=self.id,
            usuario_id=usuario_id,
            acao=acao,
            detalhes=detalhes
        )
        db.session.add(historico_entry)
        self.data_atualizacao = datetime.utcnow()
    
    def atualizar_status(self, novo_status, usuario_id=None):
        """Atualiza o status do lead e registra no histórico"""
        status_anterior = self.status
        self.status = novo_status
        self.adicionar_historico(
            acao='status_alterado',
            usuario_id=usuario_id,
            detalhes=f'Status alterado de "{status_anterior}" para "{novo_status}"'
        )
    
    def get_nivel_maturidade(self):
        """Retorna o nível de maturidade baseado na pontuação geral"""
        if self.pontuacao_geral >= 80:
            return 'Otimizado', 'success'
        elif self.pontuacao_geral >= 60:
            return 'Gerenciado', 'primary'
        elif self.pontuacao_geral >= 40:
            return 'Definido', 'info'
        elif self.pontuacao_geral >= 20:
            return 'Em Desenvolvimento', 'warning'
        else:
            return 'Inicial', 'danger'
    
    def to_dict(self):
        """Converte o lead para dicionário"""
        nivel, cor = self.get_nivel_maturidade()
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cargo': self.cargo,
            'empresa': self.empresa,
            'tipo_assessment_nome': self.tipo_assessment_nome,
            'pontuacao_geral': self.pontuacao_geral,
            'pontuacoes_dominios': self.pontuacoes_dominios,
            'status': self.status,
            'prioridade': self.prioridade,
            'nivel_maturidade': nivel,
            'nivel_cor': cor,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }


class LeadHistorico(db.Model):
    """Modelo para armazenar histórico de interações com leads"""
    
    __tablename__ = 'leads_historico'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False, comment='Lead relacionado')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), comment='Usuário que fez a ação')
    
    acao = db.Column(db.String(100), nullable=False, comment='Tipo de ação: criado, status_alterado, comentario_adicionado, etc')
    detalhes = db.Column(db.Text, comment='Detalhes da ação')
    data_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='Data do registro')
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='acoes_leads', lazy=True)
    
    def __repr__(self):
        return f'<LeadHistorico {self.id} - Lead:{self.lead_id} - {self.acao}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome if self.usuario else 'Sistema',
            'acao': self.acao,
            'detalhes': self.detalhes,
            'data_registro': self.data_registro.isoformat() if self.data_registro else None
        }
