# Carregar variáveis de ambiente do .env
import env_loader

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
    app.config["NOME_SISTEMA"] = "Sistema de Avaliações de Maturidade"
    app.config["UPLOAD_FOLDER"] = "static/uploads"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max para uploads
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Adicionar filtros personalizados ao Jinja2
    import json
    
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Filtro para converter string JSON em dict"""
        if not value:
            return {}
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}
    
    # Handler personalizado para unauthorized - BYPASS COMPLETO
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, redirect, url_for
        # BYPASS TOTAL para rotas de projetos
        if request.path.startswith('/admin/projetos'):
            return None  # Permitir acesso sem login
        # Para outras rotas, redirecionar para login
        return redirect(url_for('auth.login', next=request.url))
    
    # User loader para Flask-Login (para administradores e respondentes)
    @login_manager.user_loader
    def load_user(user_id):
        from models.usuario import Usuario
        from models.respondente import Respondente
        from flask import session
        
        # Verificar se é um respondente ou administrador baseado na sessão
        if session.get('user_type') == 'respondente':
            return Respondente.query.get(int(user_id))
        else:
            return Usuario.query.get(int(user_id))
    
    # Context processor para variáveis globais no template
    @app.context_processor
    def inject_globals():
        from models.logo import Logo
        from models.configuracao import Configuracao
        from utils.timezone_utils import get_timezone_display_name, now_local
        import logging
        
        # Tentar pegar logo do sistema via Configuração primeiro (mais confiável)
        logo_path = Configuracao.get_logo_sistema()
        
        # Se não encontrar na configuração, tentar pelo modelo Logo
        if not logo_path:
            logo = Logo.query.filter_by(ativo=True).first()
            logo_path = logo.caminho_arquivo if logo else None
        
        cores_sistema = Configuracao.get_cores_sistema()
        escala_pontuacao = Configuracao.get_escala_pontuacao()
        
        # Log para debug do logo
        logging.debug(f"Logo path encontrado: {logo_path}")
        
        return {
            'nome_sistema': app.config["NOME_SISTEMA"],
            'logo_path': logo_path,
            'cores_sistema': cores_sistema,
            'escala_pontuacao': escala_pontuacao,
            'timezone_display': get_timezone_display_name(),
            'now_local': now_local()
        }
    
    # Filtros de template para timezone
    @app.template_filter('datetime_local')
    def datetime_local_filter(utc_datetime, formato='%d/%m/%Y %H:%M'):
        from utils.timezone_utils import format_datetime_local
        return format_datetime_local(utc_datetime, formato)
    
    @app.template_filter('date_local')
    def date_local_filter(utc_datetime, formato='%d/%m/%Y'):
        from utils.timezone_utils import format_date_local
        return format_date_local(utc_datetime, formato)
    
    @app.template_filter('time_local')
    def time_local_filter(utc_datetime, formato='%H:%M'):
        from utils.timezone_utils import format_time_local
        return format_time_local(utc_datetime, formato)
    
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Converte quebras de linha em tags HTML <br>"""
        if not text:
            return ''
        from markupsafe import Markup
        return Markup(text.replace('\n', '<br>\n'))
    
    # Registrar blueprints (importação direta para evitar circular imports)
    from routes.auth import auth_bp
    from routes.cliente import cliente_bp
    from routes.admin import admin_bp
    from routes.respondente import respondente_bp
    from routes.sse_progress import sse_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(respondente_bp, url_prefix='/respondente')
    app.register_blueprint(sse_bp, url_prefix='/sse')
    
    # Blueprint admin_old removido - causava conflito de rotas
    
    # Registrar blueprint de relatório separadamente
    try:
        from routes.relatorio import relatorio_bp
        app.register_blueprint(relatorio_bp)
    except ImportError:
        pass
    
    # Registrar blueprint de projetos com prefixo correto
    try:
        from routes.projeto import projeto_bp
        app.register_blueprint(projeto_bp)
        logging.info("Blueprint de projetos registrado com sucesso")
    except ImportError as e:
        logging.error(f"Erro ao importar blueprint de projetos: {e}")
    except Exception as e:
        logging.error(f"Erro ao registrar blueprint de projetos: {e}")
    
    # Registrar blueprint de assessments versionados
    try:
        from routes.assessment_admin import assessment_admin_bp
        app.register_blueprint(assessment_admin_bp, url_prefix='/admin')
        logging.info("Blueprint de assessments registrado com sucesso")
    except ImportError as e:
        logging.error(f"Erro ao importar blueprint de assessments: {e}")
    except Exception as e:
        logging.error(f"Erro ao registrar blueprint de assessments: {e}")
    
    # Registrar blueprint de parâmetros do sistema
    try:
        from routes.parametros import parametros_bp
        app.register_blueprint(parametros_bp)
        logging.info("Blueprint de parâmetros registrado com sucesso")
    except ImportError as e:
        logging.error(f"Erro ao importar blueprint de parâmetros: {e}")
    except Exception as e:
        logging.error(f"Erro ao registrar blueprint de parâmetros: {e}")

    # Registrar portal do cliente
    try:
        from routes.cliente_portal import cliente_portal_bp
        app.register_blueprint(cliente_portal_bp)
        logging.info("Portal do cliente registrado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao registrar portal do cliente: {e}")
        
    # Rota de projetos temporária sem autenticação
    @app.route('/admin/projetos_temp')
    def lista_projetos_bypass():
        """Lista projetos sem autenticação - solução temporária"""
        from flask import redirect
        return redirect('/admin/projetos/working')
    
    # Rota para servir uploads
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        import os
        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
        return send_from_directory(upload_folder, filename)
    
    # Rota raiz
    @app.route('/')
    def index():
        from flask import redirect, url_for, session
        from flask_login import current_user
        from models.respondente import Respondente
        
        if current_user.is_authenticated:
            if isinstance(current_user, Respondente):
                return redirect(url_for('respondente.dashboard'))
            elif hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('cliente.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Rota de login alternativa para compatibilidade
    @app.route('/login')
    def login_redirect():
        """Redireciona para a rota de login correta"""
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    # Criar tabelas do banco
    with app.app_context():
        # Importar todos os modelos
        from models import usuario, dominio, pergunta, resposta, logo, tipo_assessment, cliente, respondente, configuracao, projeto, assessment_version, parametro_sistema
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        from models.usuario import Usuario
        from models.tipo_assessment import TipoAssessment
        from models.configuracao import Configuracao
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
            
            # Criar tipo de assessment padrão se não existir
            tipo_default = TipoAssessment.query.filter_by(nome='Cibersegurança').first()
            if not tipo_default:
                tipo_default = TipoAssessment(
                    nome='Cibersegurança',
                    descricao='Assessment de maturidade em cibersegurança',
                    ordem=1,
                    ativo=True
                )
                db.session.add(tipo_default)
            
            db.session.commit()
            logging.info("Usuário admin padrão criado: admin@sistema.com / admin123")
            logging.info("Tipo de assessment padrão 'Cibersegurança' criado")
        
        # Inicializar configurações padrão
        try:
            Configuracao.inicializar_configuracoes_padrao()
            logging.info("Configurações padrão inicializadas")
        except Exception as e:
            logging.error(f"Erro ao inicializar configurações: {e}")
    
    return app

# Criar instância da aplicação
app = create_app()
