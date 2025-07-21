#!/usr/bin/env python3
"""
Script para verificar e diagnosticar a configuração do ambiente on-premise
Identifica por que a aplicação está usando SQLite ao invés do PostgreSQL
"""

import os
import sys
from datetime import datetime

def check_env_file():
    """Verificar arquivo .env"""
    env_paths = ['.env', '/home/suporte/.env', '/var/www/assessment/.env']
    
    print("🔍 Verificando arquivos .env...")
    
    for path in env_paths:
        print(f"   📁 {path}: ", end="")
        if os.path.exists(path):
            print("✓ Existe")
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    print(f"      📄 Tamanho: {len(content)} caracteres")
                    
                    # Verificar se tem DATABASE_URL
                    lines = content.split('\n')
                    database_url_found = False
                    for line in lines:
                        if line.strip().startswith('DATABASE_URL'):
                            database_url_found = True
                            # Mascarar senha para exibição
                            if '@' in line:
                                parts = line.split('@')
                                masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
                                print(f"      🔗 {masked}")
                            else:
                                print(f"      🔗 {line}")
                            break
                    
                    if not database_url_found:
                        print("      ⚠️  DATABASE_URL não encontrada!")
                        
            except Exception as e:
                print(f"      ✗ Erro ao ler: {e}")
        else:
            print("✗ Não existe")
    
    return None

def check_environment_variables():
    """Verificar variáveis de ambiente"""
    print("\n🔍 Verificando variáveis de ambiente...")
    
    important_vars = [
        'DATABASE_URL',
        'SESSION_SECRET', 
        'FLASK_SECRET_KEY',
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    for var in important_vars:
        value = os.environ.get(var)
        print(f"   🔧 {var}: ", end="")
        if value:
            if 'PASSWORD' in var or 'SECRET' in var:
                print("✓ Definida (valor oculto)")
            elif 'DATABASE_URL' in var and '@' in value:
                # Mascarar senha na DATABASE_URL
                parts = value.split('@')
                masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
                print(f"✓ {masked}")
            else:
                print(f"✓ {value}")
        else:
            print("✗ Não definida")

def test_database_connection():
    """Testar qual banco de dados está sendo usado"""
    print("\n🔍 Testando conexão do banco de dados...")
    
    # Simular configuração do Flask
    database_url = os.environ.get("DATABASE_URL", "sqlite:///assessment.db")
    print(f"   🔗 URL configurada: {database_url}")
    
    if database_url.startswith('sqlite'):
        print("   ⚠️  PROBLEMA: Aplicação está configurada para SQLite!")
        print("   📝 Isso explica o erro 'no such table: auditoria'")
        return 'sqlite'
    elif database_url.startswith('postgresql'):
        print("   ✓ Aplicação está configurada para PostgreSQL")
        
        # Tentar conexão real
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),
                user=parsed.username,
                password=parsed.password
            )
            conn.close()
            print("   ✓ Conexão PostgreSQL testada com sucesso!")
            return 'postgresql_ok'
        except Exception as e:
            print(f"   ✗ Erro na conexão PostgreSQL: {e}")
            return 'postgresql_error'
    else:
        print(f"   ⚠️  URL desconhecida: {database_url}")
        return 'unknown'

def suggest_fix():
    """Sugerir correção baseada no diagnóstico"""
    print("\n🔧 DIAGNÓSTICO E CORREÇÃO:")
    print("=" * 50)
    
    # Verificar se DATABASE_URL está definida
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        print("❌ PROBLEMA: DATABASE_URL não está definida!")
        print("\n📝 SOLUÇÃO:")
        print("1. Verifique se o arquivo .env existe e está no local correto")
        print("2. Adicione a linha DATABASE_URL no .env:")
        print("   DATABASE_URL=postgresql://assessment_user:sua_senha@localhost/assessment_db")
        print("3. Reinicie o serviço:")
        print("   sudo supervisorctl restart assessment")
        
    elif database_url.startswith('sqlite'):
        print("❌ PROBLEMA: DATABASE_URL aponta para SQLite!")
        print(f"   Valor atual: {database_url}")
        print("\n📝 SOLUÇÃO:")
        print("1. Corrija a DATABASE_URL no arquivo .env:")
        print("   DATABASE_URL=postgresql://assessment_user:sua_senha@localhost/assessment_db")
        print("2. Reinicie o serviço:")
        print("   sudo supervisorctl restart assessment")
        
    elif database_url.startswith('postgresql'):
        print("✓ DATABASE_URL está configurada para PostgreSQL")
        print("✅ Próximo passo: Execute o script para criar a tabela auditoria:")
        print("   python fix_auditoria_postgresql_manual.py")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE CONFIGURAÇÃO ON-PREMISE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Diretório atual: {os.getcwd()}")
    print()
    
    check_env_file()
    check_environment_variables()
    db_status = test_database_connection()
    suggest_fix()
    
    print()
    print("=" * 60)
    print("🏁 DIAGNÓSTICO CONCLUÍDO")
    print("=" * 60)