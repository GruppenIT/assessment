from app import db
from datetime import datetime
import pytz
from flask_login import current_user
import json

class Auditoria(db.Model):
    """Modelo para registrar todas as ações do sistema"""
    __tablename__ = 'auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Usuário que realizou a ação
    usuario_tipo = db.Column(db.String(20), nullable=False)  # 'admin' ou 'respondente'
    usuario_id = db.Column(db.Integer, nullable=False)
    usuario_nome = db.Column(db.String(100), nullable=False)
    usuario_email = db.Column(db.String(100), nullable=True)
    
    # Detalhes da ação
    acao = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'delete', 'login', 'response', etc.
    entidade = db.Column(db.String(50), nullable=False)  # 'cliente', 'projeto', 'resposta', 'assessment', etc.
    entidade_id = db.Column(db.Integer, nullable=True)
    entidade_nome = db.Column(db.String(200), nullable=True)
    
    # Descrição da ação
    descricao = db.Column(db.Text, nullable=False)
    detalhes = db.Column(db.Text, nullable=True)  # JSON com detalhes extras
    
    # Metadata
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Timestamp
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Auditoria {self.id}: {self.usuario_nome} - {self.acao} {self.entidade}>'
    
    @property
    def data_hora_brasil(self):
        """Retorna a data/hora convertida para o timezone do Brasil"""
        if self.data_hora:
            utc = pytz.UTC
            brasil = pytz.timezone('America/Sao_Paulo')
            return utc.localize(self.data_hora).astimezone(brasil)
        return None
    
    @property
    def data_hora_formatada(self):
        """Retorna data/hora formatada para exibição"""
        if self.data_hora_brasil:
            return self.data_hora_brasil.strftime('%d/%m/%Y às %H:%M')
        return ''
    
    @property
    def detalhes_json(self):
        """Retorna detalhes como objeto Python"""
        if self.detalhes:
            try:
                return json.loads(self.detalhes)
            except:
                return {}
        return {}
    
    @classmethod
    def registrar(cls, acao, entidade, descricao, entidade_id=None, entidade_nome=None, 
                  detalhes=None, usuario_tipo=None, usuario_id=None, usuario_nome=None, 
                  usuario_email=None, ip_address=None, user_agent=None):
        """
        Método para registrar uma ação de auditoria
        
        Args:
            acao: Tipo da ação (create, update, delete, login, response, etc.)
            entidade: Tipo da entidade (cliente, projeto, resposta, assessment, etc.)
            descricao: Descrição legível da ação
            entidade_id: ID da entidade afetada
            entidade_nome: Nome da entidade afetada
            detalhes: Dicionário com detalhes extras (será convertido para JSON)
            usuario_tipo: 'admin' ou 'respondente'
            usuario_id: ID do usuário
            usuario_nome: Nome do usuário
            usuario_email: Email do usuário
            ip_address: IP do usuário
            user_agent: User agent do navegador
        """
        try:
            # Se não fornecido, tentar obter do usuário atual
            if not usuario_tipo and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                if hasattr(current_user, 'tipo'):
                    usuario_tipo = current_user.tipo
                elif hasattr(current_user, 'email'):
                    # Se tem email, é admin, se não, é respondente
                    usuario_tipo = 'admin' if '@' in current_user.email else 'respondente'
                else:
                    usuario_tipo = 'admin'  # padrão
                
                usuario_id = current_user.id
                usuario_nome = getattr(current_user, 'nome', getattr(current_user, 'username', 'Usuário'))
                usuario_email = getattr(current_user, 'email', None)
            
            # Converter detalhes para JSON se fornecido
            detalhes_json = None
            if detalhes:
                detalhes_json = json.dumps(detalhes, ensure_ascii=False)
            
            # Criar registro de auditoria
            auditoria = cls(
                usuario_tipo=usuario_tipo or 'sistema',
                usuario_id=usuario_id or 0,
                usuario_nome=usuario_nome or 'Sistema',
                usuario_email=usuario_email,
                acao=acao,
                entidade=entidade,
                entidade_id=entidade_id,
                entidade_nome=entidade_nome,
                descricao=descricao,
                detalhes=detalhes_json,
                ip_address=ip_address,
                user_agent=user_agent,
                data_hora=datetime.utcnow()
            )
            
            db.session.add(auditoria)
            db.session.commit()
            
            return auditoria
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao registrar auditoria: {e}")
            return None
    
    @classmethod
    def obter_atividades_recentes(cls, limite=50):
        """Obtém as atividades mais recentes para o dashboard"""
        return cls.query.order_by(cls.data_hora.desc()).limit(limite).all()
    
    @classmethod
    def obter_atividades_por_usuario(cls, usuario_tipo, usuario_id, limite=50):
        """Obtém atividades de um usuário específico"""
        return cls.query.filter_by(
            usuario_tipo=usuario_tipo,
            usuario_id=usuario_id
        ).order_by(cls.data_hora.desc()).limit(limite).all()
    
    @classmethod
    def obter_atividades_por_entidade(cls, entidade, entidade_id, limite=50):
        """Obtém atividades relacionadas a uma entidade específica"""
        return cls.query.filter_by(
            entidade=entidade,
            entidade_id=entidade_id
        ).order_by(cls.data_hora.desc()).limit(limite).all()
    
    @classmethod
    def estatisticas_dashboard(cls):
        """Retorna estatísticas para o dashboard"""
        from datetime import datetime, timedelta
        
        hoje = datetime.utcnow().date()
        semana_passada = hoje - timedelta(days=7)
        mes_passado = hoje - timedelta(days=30)
        
        return {
            'total_acoes': cls.query.count(),
            'acoes_hoje': cls.query.filter(
                db.func.date(cls.data_hora) == hoje
            ).count(),
            'acoes_semana': cls.query.filter(
                cls.data_hora >= semana_passada
            ).count(),
            'acoes_mes': cls.query.filter(
                cls.data_hora >= mes_passado
            ).count(),
            'usuarios_ativos_hoje': db.session.query(cls.usuario_id).filter(
                db.func.date(cls.data_hora) == hoje
            ).distinct().count(),
            'ultimas_acoes': cls.query.order_by(cls.data_hora.desc()).limit(10).all()
        }

# Funções auxiliares para registrar ações específicas

def registrar_login(usuario_tipo, usuario_id, usuario_nome, usuario_email=None, ip_address=None):
    """Registra login de usuário"""
    return Auditoria.registrar(
        acao='login',
        entidade='sistema',
        descricao=f'{usuario_nome} fez login no sistema',
        usuario_tipo=usuario_tipo,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        usuario_email=usuario_email,
        ip_address=ip_address
    )

def registrar_logout(usuario_tipo, usuario_id, usuario_nome, usuario_email=None):
    """Registra logout de usuário"""
    return Auditoria.registrar(
        acao='logout',
        entidade='sistema',
        descricao=f'{usuario_nome} fez logout do sistema',
        usuario_tipo=usuario_tipo,
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        usuario_email=usuario_email
    )

def registrar_resposta(projeto_id, projeto_nome, pergunta_id, pergunta_texto, 
                      valor_anterior=None, valor_novo=None):
    """Registra resposta de assessment"""
    descricao = f'Respondeu pergunta em "{projeto_nome}"'
    
    detalhes = {
        'pergunta_id': pergunta_id,
        'pergunta_texto': pergunta_texto[:100] + '...' if len(pergunta_texto) > 100 else pergunta_texto,
        'valor_anterior': valor_anterior,
        'valor_novo': valor_novo
    }
    
    return Auditoria.registrar(
        acao='response',
        entidade='projeto',
        entidade_id=projeto_id,
        entidade_nome=projeto_nome,
        descricao=descricao,
        detalhes=detalhes
    )

def registrar_criacao(entidade, entidade_id, entidade_nome, detalhes=None):
    """Registra criação de entidade"""
    return Auditoria.registrar(
        acao='create',
        entidade=entidade,
        entidade_id=entidade_id,
        entidade_nome=entidade_nome,
        descricao=f'Criou {entidade}: {entidade_nome}',
        detalhes=detalhes
    )

def registrar_edicao(entidade, entidade_id, entidade_nome, detalhes=None):
    """Registra edição de entidade"""
    return Auditoria.registrar(
        acao='update',
        entidade=entidade,
        entidade_id=entidade_id,
        entidade_nome=entidade_nome,
        descricao=f'Editou {entidade}: {entidade_nome}',
        detalhes=detalhes
    )

def registrar_exclusao(entidade, entidade_id, entidade_nome, detalhes=None):
    """Registra exclusão de entidade"""
    return Auditoria.registrar(
        acao='delete',
        entidade=entidade,
        entidade_id=entidade_id,
        entidade_nome=entidade_nome,
        descricao=f'Excluiu {entidade}: {entidade_nome}',
        detalhes=detalhes
    )