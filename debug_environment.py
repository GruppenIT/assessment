#!/usr/bin/env python3
"""
Script para debugar exatamente o que está acontecendo com as variáveis de ambiente
"""

import os
import sys
from datetime import datetime

def check_all_environments():
    """Verificar todas as formas possíveis de variáveis de ambiente"""
    
    print("🔍 Verificando variáveis de ambiente em diferentes contextos...")
    
    # 1. Variáveis de ambiente do processo atual
    print("\n1. Variáveis do processo Python atual:")
    important_vars = ['DATABASE_URL', 'SESSION_SECRET', 'FLASK_SECRET_KEY']
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            if 'DATABASE_URL' in var and '@' in value:
                parts = value.split('@')
                masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
                print(f"   ✓ {var}={masked}")
            elif 'SECRET' in var:
                print(f"   ✓ {var}=***")
            else:
                print(f"   ✓ {var}={value}")
        else:
            print(f"   ✗ {var}=None")
    
    # 2. Verificar arquivo .env
    print("\n2. Conteúdo do arquivo .env:")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            content = f.read()
            print(f"   📄 Tamanho: {len(content)} bytes")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#') and '=' in line:
                    key = line.split('=')[0]
                    if key in important_vars:
                        if 'DATABASE_URL' in key and '@' in line:
                            parts = line.split('@')
                            masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
                            print(f"   📝 {masked}")
                        elif 'SECRET' in key:
                            print(f"   📝 {key}=***")
                        else:
                            print(f"   📝 {line}")
    else:
        print("   ✗ Arquivo .env não existe")
    
    # 3. Simular configuração do Flask
    print("\n3. Simulação da configuração Flask:")
    database_url_env = os.environ.get("DATABASE_URL", "sqlite:///assessment.db")
    print(f"   🔗 DATABASE_URL do environment: {database_url_env}")
    print(f"   📁 Diretório atual: {os.getcwd()}")
    
    return database_url_env

def load_env_manually():
    """Carregar .env manualmente e testar"""
    
    print("\n4. Carregamento manual do .env:")
    
    if not os.path.exists('.env'):
        print("   ✗ .env não existe")
        return None
        
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip('\'"')
    
    database_url = env_vars.get('DATABASE_URL')
    if database_url:
        if '@' in database_url:
            parts = database_url.split('@')
            masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
            print(f"   📝 DATABASE_URL do .env: {masked}")
        else:
            print(f"   📝 DATABASE_URL do .env: {database_url}")
        
        # Aplicar no environment atual
        os.environ['DATABASE_URL'] = database_url
        print(f"   ✓ DATABASE_URL aplicada no environment")
        
        return database_url
    else:
        print("   ✗ DATABASE_URL não encontrada no .env")
        return None

def test_flask_with_manual_env():
    """Testar Flask após carregar .env manualmente"""
    
    print("\n5. Teste Flask após carregamento manual:")
    
    try:
        # Carregar manualmente primeiro
        database_url = load_env_manually()
        
        if not database_url:
            print("   ✗ Não conseguiu carregar DATABASE_URL")
            return False
            
        # Testar Flask
        from app import create_app
        app = create_app()
        
        with app.app_context():
            configured_url = app.config.get('SQLALCHEMY_DATABASE_URI')
            print(f"   🔗 Flask DATABASE_URI: {configured_url}")
            
            if configured_url and configured_url.startswith('postgresql'):
                print("   ✅ Flask agora configurado para PostgreSQL!")
                
                # Testar conexão
                from app import db
                try:
                    result = db.session.execute(db.text("SELECT version()")).fetchone()
                    print(f"   ✅ PostgreSQL conectado: {result[0][:50]}...")
                    return True
                except Exception as e:
                    print(f"   ✗ Erro na conexão PostgreSQL: {e}")
                    return False
            else:
                print(f"   ❌ Flask ainda usando: {configured_url}")
                return False
                
    except Exception as e:
        print(f"   ✗ Erro no teste Flask: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 DEBUG COMPLETO DE ENVIRONMENT")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar tudo
    check_all_environments()
    
    # Testar carregamento manual
    success = test_flask_with_manual_env()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ PROBLEMA RESOLVIDO COM CARREGAMENTO MANUAL!")
        print("📝 Próximo passo: aplicar correção permanente")
    else:
        print("❌ PROBLEMA PERSISTE")
        print("📝 Investigação adicional necessária")
    print("=" * 60)