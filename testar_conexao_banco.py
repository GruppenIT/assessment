#!/usr/bin/env python3
"""
Script para testar conexão com o banco de dados PostgreSQL
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def testar_conexao_banco():
    """Testa a conexão com o banco usando diferentes formatos de URL"""
    
    print("🔍 TESTE DE CONEXÃO COM BANCO DE DADOS")
    print("="*50)
    
    # URLs para testar
    urls_teste = [
        "postgresql://assessment_user:P@ssw0rd@.!@localhost/assessment_db",
        "postgresql://assessment_user:P%40ssw0rd%40.%21@localhost/assessment_db",
        "postgresql://assessment_user:P\\@ssw0rd\\@.\\!@localhost/assessment_db"
    ]
    
    for i, url in enumerate(urls_teste, 1):
        print(f"\n📝 Teste {i}: {url}")
        
        try:
            # Parse da URL
            parsed = urlparse(url)
            print(f"   Host: {parsed.hostname}")
            print(f"   Porta: {parsed.port or 5432}")
            print(f"   Usuario: {parsed.username}")
            print(f"   Senha: {'*' * len(parsed.password) if parsed.password else 'None'}")
            print(f"   Database: {parsed.path.lstrip('/')}")
            
            # Tentar conexão
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/')
            )
            
            # Testar query simples
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            print(f"   ✅ CONEXÃO SUCESSO!")
            print(f"   📦 PostgreSQL: {version[0][:50]}...")
            
            cursor.close()
            conn.close()
            
            return url
            
        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
            
    return None

def verificar_env_atual():
    """Verifica qual URL está sendo usada atualmente"""
    
    print("\n🔍 VERIFICANDO ARQUIVO .env ATUAL")
    print("="*40)
    
    env_files = ['/var/www/assessment/.env', '.env']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"\n📄 Arquivo: {env_file}")
            try:
                with open(env_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        if line.strip().startswith('DATABASE_URL'):
                            print(f"   Linha {line_num}: {line.strip()}")
            except Exception as e:
                print(f"   ❌ Erro ao ler: {e}")

if __name__ == "__main__":
    verificar_env_atual()
    
    url_funcionando = testar_conexao_banco()
    
    if url_funcionando:
        print(f"\n🎉 URL FUNCIONAL ENCONTRADA:")
        print(f"   {url_funcionando}")
        print(f"\n💡 Use esta URL no arquivo .env para resolver o problema")
    else:
        print(f"\n⚠️ NENHUMA URL FUNCIONOU")
        print(f"   Verifique se o PostgreSQL está rodando")
        print(f"   Verifique se o usuário e senha estão corretos")
        print(f"   Comando: sudo systemctl status postgresql")