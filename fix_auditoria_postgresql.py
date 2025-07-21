#!/usr/bin/env python3
"""
Script para criar a tabela de auditoria no PostgreSQL (ambiente on-premise)
Execute este script no diretório da aplicação para resolver o erro
"""

import os
import sys
import psycopg2
from datetime import datetime

def get_database_config():
    """Obter configuração do banco PostgreSQL"""
    
    # Tentar obter do .env ou variáveis de ambiente
    db_config = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
        'database': os.environ.get('DB_NAME', 'assessment_db'),
        'user': os.environ.get('DB_USER', 'assessment_user'),
        'password': os.environ.get('DB_PASSWORD', '')
    }
    
    # Tentar ler do arquivo .env se existir
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key == 'DB_HOST':
                        db_config['host'] = value
                    elif key == 'DB_PORT':
                        db_config['port'] = value
                    elif key == 'DB_NAME':
                        db_config['database'] = value
                    elif key == 'DB_USER':
                        db_config['user'] = value
                    elif key == 'DB_PASSWORD':
                        db_config['password'] = value
    
    return db_config

def create_auditoria_table():
    """Criar tabela de auditoria no PostgreSQL"""
    
    db_config = get_database_config()
    print(f"📂 Conectando no PostgreSQL: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
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

def create_configuracoes_table():
    """Criar tabela de configurações se não existir"""
    
    db_config = get_database_config()
    
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
    print("🔄 MIGRAÇÃO ON-PREMISE POSTGRESQL - TABELAS AUDITORIA")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Diretório atual: {os.getcwd()}")
    print()
    
    success = True
    
    if not create_auditoria_table():
        success = False
    
    print()
    
    if not create_configuracoes_table():
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