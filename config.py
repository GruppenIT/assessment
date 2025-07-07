import os

class Config:
    """Configurações da aplicação"""
    
    # Configurações básicas
    SECRET_KEY = os.environ.get('SESSION_SECRET') or 'chave-secreta-desenvolvimento'
    
    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///assessment.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Upload de arquivos
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Sistema
    NOME_SISTEMA = "Sistema de Assessment de Cibersegurança"
    
    # Extensões permitidas para upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False

# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
