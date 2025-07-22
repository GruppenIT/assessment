#!/usr/bin/env python3
"""
Script para aplicar as variáveis do .env permanentemente na aplicação
Modifica o código para carregar .env no início da execução
"""

import os
import sys
from datetime import datetime

def create_env_loader():
    """Criar módulo para carregar .env automaticamente"""
    
    env_loader_content = '''"""
Carregador de variáveis de ambiente do arquivo .env
Este módulo é importado no início da aplicação para garantir
que as variáveis do .env sejam sempre carregadas
"""

import os

def load_env():
    """Carregar variáveis do arquivo .env"""
    env_files = ['.env', '/home/suporte/.env']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remover aspas se existirem
                            value = value.strip('\'"')
                            # Aplicar no environment
                            os.environ[key] = value
                print(f"ENV_LOADER: Carregadas variáveis de {env_file}")
                return True
            except Exception as e:
                print(f"ENV_LOADER: Erro ao carregar {env_file}: {e}")
                continue
    
    print("ENV_LOADER: Nenhum arquivo .env encontrado")
    return False

# Carregar automaticamente quando este módulo for importado
load_env()
'''
    
    with open('env_loader.py', 'w') as f:
        f.write(env_loader_content)
    
    print("✓ Módulo env_loader.py criado")

def modify_main_py():
    """Modificar main.py para importar env_loader primeiro"""
    
    if not os.path.exists('main.py'):
        print("✗ main.py não encontrado")
        return False
    
    # Ler conteúdo atual
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Verificar se já foi modificado
    if 'import env_loader' in content:
        print("✓ main.py já modificado")
        return True
    
    # Fazer backup
    backup_file = f"main.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"💾 Backup: {backup_file}")
    
    # Adicionar import no início
    new_content = "# Carregar variáveis de ambiente do .env\nimport env_loader\n\n" + content
    
    with open('main.py', 'w') as f:
        f.write(new_content)
    
    print("✓ main.py modificado para carregar .env")
    return True

def modify_app_py():
    """Modificar app.py para importar env_loader primeiro"""
    
    if not os.path.exists('app.py'):
        print("✗ app.py não encontrado")
        return False
    
    # Ler conteúdo atual
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Verificar se já foi modificado
    if 'import env_loader' in content:
        print("✓ app.py já modificado")
        return True
    
    # Fazer backup
    backup_file = f"app.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"💾 Backup: {backup_file}")
    
    # Adicionar import no início
    new_content = "# Carregar variáveis de ambiente do .env\nimport env_loader\n\n" + content
    
    with open('app.py', 'w') as f:
        f.write(new_content)
    
    print("✓ app.py modificado para carregar .env")
    return True

def test_modified_application():
    """Testar aplicação modificada"""
    
    print("\n🧪 Testando aplicação modificada...")
    
    try:
        # Reimportar módulos para pegar as modificações
        if 'app' in sys.modules:
            del sys.modules['app']
        if 'env_loader' in sys.modules:
            del sys.modules['env_loader']
        
        # Importar novamente
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
            print(f"   🔗 DATABASE_URI: {database_url}")
            
            if database_url and database_url.startswith('postgresql'):
                print("   ✅ Aplicação configurada para PostgreSQL!")
                
                # Testar conexão
                from app import db
                try:
                    result = db.session.execute(db.text("SELECT version()")).fetchone()
                    print(f"   ✅ PostgreSQL conectado: {result[0][:50]}...")
                    return True
                except Exception as e:
                    print(f"   ✗ Erro na conexão: {e}")
                    return False
            else:
                print(f"   ❌ Ainda usando: {database_url}")
                return False
                
    except Exception as e:
        print(f"   ✗ Erro no teste: {e}")
        return False

def restart_supervisor():
    """Reiniciar supervisor"""
    
    print("\n🔄 Reiniciando supervisor...")
    
    try:
        result = os.system("sudo supervisorctl restart assessment")
        if result == 0:
            print("   ✅ Supervisor reiniciado")
            return True
        else:
            print(f"   ⚠️  Código de saída: {result}")
            return False
    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 APLICAÇÃO PERMANENTE DO .ENV")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Criar módulo carregador
    create_env_loader()
    
    # Modificar arquivos principais
    modify_main_py()
    modify_app_py()
    
    # Testar localmente
    if test_modified_application():
        print("✅ Teste local funcionou!")
    else:
        print("⚠️  Teste local com problemas")
    
    # Reiniciar supervisor
    restart_supervisor()
    
    print("\n" + "=" * 60)
    print("✅ CORREÇÃO PERMANENTE APLICADA")
    print("📝 Agora a aplicação sempre carregará o .env automaticamente")
    print("🔄 Aguarde alguns segundos e teste novamente")
    print("=" * 60)