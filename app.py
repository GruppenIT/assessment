import os
import logging
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configurar logging para debug
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Instâncias globais
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    """Factory para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.secret_key = os.environ.get("SESSION_SECRET", "chave-secreta-desenvolvimento")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configuração do banco de dados
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///assessment.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Configurações específicas do sistema
    app.config["NOME_SISTEMA"] = "Sistema de Assessment de Cibersegurança"
    app.config["UPLOAD_FOLDER"] = "static/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max para uploads
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.usuario import Usuario
        return Usuario.query.get(int(user_id))
    
    # Context processor para variáveis globais no template
    @app.context_processor
    def inject_globals():
        from models.logo import Logo
        logo = Logo.query.first()
        return {
            'nome_sistema': app.config["NOME_SISTEMA"],
            'logo_path': logo.caminho_arquivo if logo else None
        }
    
    # Registrar blueprints (importação direta para evitar circular imports)
    from routes.auth import auth_bp
    from routes.cliente import cliente_bp
    from routes.admin import admin_bp
    from routes.relatorio import relatorio_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(relatorio_bp, url_prefix='/relatorio')
    
    # Rota raiz
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        
        if current_user.is_authenticated:
            if current_user.tipo == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('cliente.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Criar tabelas do banco
    with app.app_context():
        # Importar todos os modelos
        from models import usuario, dominio, pergunta, resposta, logo
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        from models.usuario import Usuario
        from werkzeug.security import generate_password_hash
        
        admin_existente = Usuario.query.filter_by(email='admin@sistema.com').first()
        if not admin_existente:
            admin = Usuario(
                nome='Administrador',
                email='admin@sistema.com',
                senha_hash=generate_password_hash('admin123'),
                tipo='admin'
            )
            db.session.add(admin)
            db.session.commit()
            logging.info("Usuário admin padrão criado: admin@sistema.com / admin123")
    
    return app

# Criar instância da aplicação
app = create_app()
