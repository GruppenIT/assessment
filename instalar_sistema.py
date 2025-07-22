#!/usr/bin/env python3
"""
Script de instalação do Sistema de Avaliações de Maturidade
Configura banco de dados, cria usuário admin e tabelas necessárias
"""

import os
import sys
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# Carregar variáveis de ambiente
import env_loader

def verificar_ambiente():
    """Verificar se ambiente está configurado corretamente"""
    
    print("🔍 Verificando ambiente...")
    
    # Verificar variáveis essenciais
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não configurada")
        return False
    
    if not database_url.startswith('postgresql'):
        print(f"❌ DATABASE_URL deve ser PostgreSQL: {database_url}")
        return False
    
    session_secret = os.environ.get('SESSION_SECRET')
    if not session_secret or len(session_secret) < 32:
        print("❌ SESSION_SECRET deve ter pelo menos 32 caracteres")
        return False
    
    print("✅ Ambiente configurado corretamente")
    return True

def testar_conexao_banco():
    """Testar conexão com PostgreSQL"""
    
    print("🔗 Testando conexão com banco de dados...")
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        parsed = urlparse(database_url)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        conn.close()
        print(f"✅ PostgreSQL conectado: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def criar_tabelas():
    """Criar todas as tabelas necessárias"""
    
    print("🏗️ Criando tabelas do sistema...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Importar todos os modelos
            import models.usuario
            import models.cliente
            import models.respondente
            import models.tipo_assessment
            import models.dominio
            import models.pergunta
            import models.resposta
            import models.projeto
            import models.auditoria
            import models.configuracao
            import models.logo
            import models.assessment_versioning
            
            # Criar tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def criar_usuario_admin():
    """Criar usuário administrador padrão"""
    
    print("👤 Criando usuário administrador...")
    
    try:
        from app import create_app, db
        from models.usuario import Usuario
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        
        with app.app_context():
            # Verificar se já existe admin
            admin_existente = Usuario.query.filter_by(email='admin@sistema.com').first()
            if admin_existente:
                print("✅ Usuário admin já existe")
                return True
            
            # Criar novo admin
            admin = Usuario(
                nome='Administrador',
                email='admin@sistema.com',
                senha_hash=generate_password_hash('admin123')
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário admin criado:")
            print("   Email: admin@sistema.com")
            print("   Senha: admin123")
            print("   ⚠️  ALTERE A SENHA NO PRIMEIRO ACESSO!")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        return False

def criar_configuracoes_padrao():
    """Criar configurações padrão do sistema"""
    
    print("⚙️ Criando configurações padrão...")
    
    try:
        from app import create_app, db
        from models.configuracao import Configuracao
        
        app = create_app()
        
        with app.app_context():
            configuracoes_padrao = [
                {
                    'chave': 'nome_sistema',
                    'valor': 'Sistema de Avaliações de Maturidade',
                    'descricao': 'Nome do sistema exibido na interface'
                },
                {
                    'chave': 'versao_sistema',
                    'valor': '2.0',
                    'descricao': 'Versão atual do sistema'
                },
                {
                    'chave': 'timezone',
                    'valor': 'America/Sao_Paulo',
                    'descricao': 'Timezone padrão do sistema'
                },
                {
                    'chave': 'email_suporte',
                    'valor': 'suporte@empresa.com',
                    'descricao': 'Email para contato de suporte'
                },
                {
                    'chave': 'max_upload_size',
                    'valor': '16777216',  # 16MB
                    'descricao': 'Tamanho máximo para upload de arquivos (bytes)'
                }
            ]
            
            for config in configuracoes_padrao:
                existing = Configuracao.query.filter_by(chave=config['chave']).first()
                if not existing:
                    nova_config = Configuracao(
                        chave=config['chave'],
                        valor=config['valor'],
                        descricao=config['descricao']
                    )
                    db.session.add(nova_config)
            
            db.session.commit()
            print("✅ Configurações padrão criadas")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar configurações: {e}")
        return False

def criar_tipo_assessment_padrao():
    """Criar tipo de assessment padrão"""
    
    print("📋 Criando tipo de assessment padrão...")
    
    try:
        from app import create_app, db
        from models.assessment_versioning import AssessmentTipo
        
        app = create_app()
        
        with app.app_context():
            # Verificar se já existe
            tipo_existente = AssessmentTipo.query.filter_by(nome='Cibersegurança').first()
            if tipo_existente:
                print("✅ Tipo de assessment padrão já existe")
                return True
            
            # Criar tipo padrão
            tipo_padrao = AssessmentTipo(
                nome='Cibersegurança',
                descricao='Avaliação de maturidade em cibersegurança baseada em frameworks como NIST, ISO27001 e CIS'
            )
            
            db.session.add(tipo_padrao)
            db.session.commit()
            
            print("✅ Tipo de assessment 'Cibersegurança' criado")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar tipo de assessment: {e}")
        return False

def verificar_instalacao():
    """Verificar se instalação foi bem-sucedida"""
    
    print("🧪 Verificando instalação...")
    
    try:
        from app import create_app, db
        from models.usuario import Usuario
        from models.configuracao import Configuracao
        from models.assessment_versioning import AssessmentTipo
        
        app = create_app()
        
        with app.app_context():
            # Verificar tabelas
            result = db.session.execute(db.text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            count = result.fetchone()[0]
            
            if count < 10:
                print(f"⚠️ Apenas {count} tabelas encontradas (esperado: 10+)")
                return False
            
            # Verificar usuário admin
            admin = Usuario.query.filter_by(email='admin@sistema.com').first()
            if not admin:
                print("❌ Usuário admin não encontrado")
                return False
            
            # Verificar configurações
            configs = Configuracao.query.count()
            if configs < 3:
                print(f"⚠️ Apenas {configs} configurações encontradas")
                return False
            
            # Verificar tipo de assessment
            tipo = AssessmentTipo.query.first()
            if not tipo:
                print("❌ Nenhum tipo de assessment encontrado")
                return False
            
            print("✅ Instalação verificada com sucesso")
            print(f"   📊 {count} tabelas criadas")
            print(f"   👤 Usuário admin configurado")
            print(f"   ⚙️ {configs} configurações padrão")
            print(f"   📋 Tipo de assessment disponível")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def main():
    """Função principal de instalação"""
    
    print("=" * 60)
    print("🚀 INSTALAÇÃO DO SISTEMA DE AVALIAÇÕES DE MATURIDADE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Verificar ambiente
    if not verificar_ambiente():
        print("\n❌ Ambiente não configurado corretamente")
        print("📝 Verifique o arquivo .env e as variáveis de ambiente")
        sys.exit(1)
    
    print()
    
    # Testar banco
    if not testar_conexao_banco():
        print("\n❌ Não foi possível conectar ao banco de dados")
        print("📝 Verifique se PostgreSQL está rodando e configurado")
        sys.exit(1)
    
    print()
    
    # Criar estrutura
    steps = [
        ("Criar tabelas", criar_tabelas),
        ("Criar usuário admin", criar_usuario_admin),
        ("Criar configurações padrão", criar_configuracoes_padrao),
        ("Criar tipo de assessment", criar_tipo_assessment_padrao),
        ("Verificar instalação", verificar_instalacao)
    ]
    
    for step_name, step_func in steps:
        print(f"📋 {step_name}...")
        if not step_func():
            print(f"\n❌ Falha em: {step_name}")
            sys.exit(1)
        print()
    
    print("=" * 60)
    print("🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("🌐 Acesse o sistema pelo navegador")
    print("👤 Login: admin@sistema.com")
    print("🔑 Senha: admin123")
    print("⚠️  IMPORTANTE: Altere a senha no primeiro acesso!")
    print("=" * 60)

if __name__ == "__main__":
    main()