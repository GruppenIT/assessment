from datetime import datetime
from app import db

class Configuracao(db.Model):
    """Modelo para configurações do sistema"""
    
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False, comment='Chave da configuração')
    valor = db.Column(db.Text, comment='Valor da configuração')
    descricao = db.Column(db.String(500), comment='Descrição da configuração')
    tipo = db.Column(db.String(50), default='string', comment='Tipo do valor (string, color, number, boolean)')
    categoria = db.Column(db.String(50), default='geral', comment='Categoria da configuração')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, comment='Data de criação')
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Data da última atualização')
    
    def __repr__(self):
        return f'<Configuracao {self.chave}={self.valor}>'
    
    @staticmethod
    def get_valor(chave, default=None):
        """Obter valor de uma configuração"""
        config = Configuracao.query.filter_by(chave=chave).first()
        return config.valor if config else default
    
    @staticmethod
    def set_valor(chave, valor, descricao=None, tipo='string', categoria='geral'):
        """Definir valor de uma configuração"""
        config = Configuracao.query.filter_by(chave=chave).first()
        
        if config:
            config.valor = valor
            config.data_atualizacao = datetime.utcnow()
        else:
            config = Configuracao(
                chave=chave,
                valor=valor,
                descricao=descricao,
                tipo=tipo,
                categoria=categoria
            )
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @staticmethod
    def get_configuracoes_categoria(categoria):
        """Obter todas as configurações de uma categoria"""
        return Configuracao.query.filter_by(categoria=categoria).all()
    
    @staticmethod
    def inicializar_configuracoes_padrao():
        """Inicializar configurações padrão do sistema"""
        configuracoes_padrao = [
            # Cores do sistema
            ('cor_primaria', '#0d6efd', 'Cor primária do sistema', 'color', 'aparencia'),
            ('cor_secundaria', '#6c757d', 'Cor secundária do sistema', 'color', 'aparencia'),
            ('cor_sucesso', '#198754', 'Cor de sucesso', 'color', 'aparencia'),
            ('cor_perigo', '#dc3545', 'Cor de perigo/erro', 'color', 'aparencia'),
            ('cor_aviso', '#ffc107', 'Cor de aviso', 'color', 'aparencia'),
            ('cor_info', '#0dcaf0', 'Cor de informação', 'color', 'aparencia'),
            ('cor_fundo', '#ffffff', 'Cor de fundo', 'color', 'aparencia'),
            ('cor_texto', '#212529', 'Cor do texto', 'color', 'aparencia'),
            
            # Configurações gerais
            ('tema_escuro', 'false', 'Habilitar tema escuro', 'boolean', 'aparencia'),
            ('logo_navbar', 'true', 'Exibir logo na barra de navegação', 'boolean', 'aparencia'),
            ('sidebar_fechada', 'false', 'Sidebar fechada por padrão', 'boolean', 'aparencia'),
        ]
        
        for chave, valor, descricao, tipo, categoria in configuracoes_padrao:
            existing = Configuracao.query.filter_by(chave=chave).first()
            if not existing:
                config = Configuracao(
                    chave=chave,
                    valor=valor,
                    descricao=descricao,
                    tipo=tipo,
                    categoria=categoria
                )
                db.session.add(config)
        
        db.session.commit()
    
    def to_dict(self):
        """Converte a configuração para dicionário"""
        return {
            'id': self.id,
            'chave': self.chave,
            'valor': self.valor,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }