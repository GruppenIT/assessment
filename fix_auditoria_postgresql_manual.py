#!/usr/bin/env python3
"""
Script para criar a tabela de auditoria no PostgreSQL com entrada manual de credenciais
Use quando o .env não estiver configurado corretamente
"""

import os
import sys
import psycopg2
import getpass
from datetime import datetime

def get_manual_config():
    """Obter configuração manual do banco PostgreSQL"""
    
    print("📋 Configure as credenciais do PostgreSQL:")
    print("   (deixe em branco para usar valores padrão)")
    print()
    
    host = input("Host [localhost]: ").strip() or 'localhost'
    port = input("Port [5432]: ").strip() or '5432'
    database = input("Database [assessment_db]: ").strip() or 'assessment_db'
    user = input("User [assessment_user]: ").strip() or 'assessment_user'
    password = getpass.getpass("Password: ")
    
    return {
        'host': host,
        'port': int(port),
        'database': database,
        'user': user,
        'password': password
    }

def test_connection(db_config):
    """Testar conexão com PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        conn.close()
        print("✓ Conexão PostgreSQL testada com sucesso!")
        return True
    except Exception as e:
        print(f"✗ Erro na conexão: {e}")
        return False

def create_auditoria_table(db_config):
    """Criar tabela de auditoria no PostgreSQL"""
    
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auditoria'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✓ Tabela auditoria já existe")
            return True
        
        print("🔨 Criando tabela auditoria...")
        
        # Criar tabela auditoria
        cursor.execute("""
            CREATE TABLE auditoria (
                id SERIAL PRIMARY KEY,
                usuario_tipo VARCHAR(50),
                usuario_id INTEGER,
                usuario_nome VARCHAR(200),
                usuario_email VARCHAR(200),
                acao VARCHAR(100) NOT NULL,
                entidade VARCHAR(100) NOT NULL,
                entidade_id INTEGER,
                entidade_nome VARCHAR(300),
                descricao TEXT,
                detalhes TEXT,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Criar índices para performance
        cursor.execute("CREATE INDEX ix_auditoria_usuario_id ON auditoria (usuario_id);")
        cursor.execute("CREATE INDEX ix_auditoria_entidade ON auditoria (entidade);")
        cursor.execute("CREATE INDEX ix_auditoria_data_hora ON auditoria (data_hora);")
        cursor.execute("CREATE INDEX ix_auditoria_acao ON auditoria (acao);")
        
        conn.commit()
        print("✓ Tabela auditoria criada com sucesso!")
        print("✓ Índices criados com sucesso!")
        
        # Verificar se foi criada
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auditoria'
            );
        """)
        if cursor.fetchone()[0]:
            print("✓ Verificação: Tabela auditoria confirmada no banco")
        else:
            print("✗ Verificação: Tabela não foi criada corretamente")
            return False
        
    except Exception as e:
        print(f"✗ Erro ao criar tabela auditoria: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

def create_configuracoes_table(db_config):
    """Criar tabela de configurações se não existir"""
    
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'configuracoes'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✓ Tabela configuracoes já existe")
            return True
        
        print("🔨 Criando tabela configuracoes...")
        
        # Criar tabela configuracoes
        cursor.execute("""
            CREATE TABLE configuracoes (
                id SERIAL PRIMARY KEY,
                chave VARCHAR(100) NOT NULL UNIQUE,
                valor TEXT,
                descricao VARCHAR(500),
                tipo VARCHAR(50) DEFAULT 'string',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("✓ Tabela configuracoes criada com sucesso!")
        
    except Exception as e:
        print(f"✗ Erro ao criar tabela configuracoes: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MIGRAÇÃO POSTGRESQL MANUAL - TABELAS AUDITORIA")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Obter configurações manualmente
    db_config = get_manual_config()
    
    print()
    print(f"📂 Testando conexão com: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    if not test_connection(db_config):
        print("❌ Não foi possível conectar ao PostgreSQL")
        sys.exit(1)
    
    print()
    
    success = True
    
    if not create_auditoria_table(db_config):
        success = False
    
    print()
    
    if not create_configuracoes_table(db_config):
        success = False
    
    print()
    print("=" * 60)
    if success:
        print("✅ MIGRAÇÃO POSTGRESQL CONCLUÍDA COM SUCESSO!")
        print("🔄 Reinicie o serviço: sudo supervisorctl restart assessment")
    else:
        print("❌ MIGRAÇÃO CONCLUÍDA COM ERROS")
        sys.exit(1)
    print("=" * 60)