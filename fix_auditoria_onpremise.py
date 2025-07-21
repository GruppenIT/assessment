#!/usr/bin/env python3
"""
Script para criar a tabela de auditoria no ambiente on-premise
Execute este script no diretório da aplicação para resolver o erro
"""

import os
import sys
import sqlite3
from datetime import datetime

def find_database_path():
    """Encontrar o caminho correto do banco de dados SQLite"""
    possible_paths = [
        'instance/database.db',
        'database.db',
        '../instance/database.db',
        '/var/www/assessment/instance/database.db'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
        
        # Tentar criar o diretório se não existir
        if 'instance' in path and not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
                return path
            except:
                continue
    
    # Se não encontrou, usar o padrão
    return 'instance/database.db'

def create_auditoria_table():
    """Criar tabela de auditoria no SQLite"""
    
    db_path = find_database_path()
    print(f"📂 Usando banco de dados: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='auditoria'
        """)
        
        if cursor.fetchone():
            print("✓ Tabela auditoria já existe")
            return True
        
        print("🔨 Criando tabela auditoria...")
        
        # Criar tabela auditoria
        cursor.execute("""
            CREATE TABLE auditoria (
                id INTEGER NOT NULL,
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
                data_hora DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
        """)
        
        # Criar índices para performance
        cursor.execute("CREATE INDEX ix_auditoria_usuario_id ON auditoria (usuario_id)")
        cursor.execute("CREATE INDEX ix_auditoria_entidade ON auditoria (entidade)")
        cursor.execute("CREATE INDEX ix_auditoria_data_hora ON auditoria (data_hora)")
        cursor.execute("CREATE INDEX ix_auditoria_acao ON auditoria (acao)")
        
        conn.commit()
        print("✓ Tabela auditoria criada com sucesso!")
        print("✓ Índices criados com sucesso!")
        
        # Verificar se foi criada
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auditoria'")
        if cursor.fetchone():
            print("✓ Verificação: Tabela auditoria confirmada no banco")
        else:
            print("✗ Verificação: Tabela não foi criada corretamente")
            return False
        
    except Exception as e:
        print(f"✗ Erro ao criar tabela auditoria: {e}")
        return False
    finally:
        conn.close()
    
    return True

def create_configuracoes_table():
    """Criar tabela de configurações se não existir"""
    
    db_path = find_database_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='configuracoes'
        """)
        
        if cursor.fetchone():
            print("✓ Tabela configuracoes já existe")
            return True
        
        print("🔨 Criando tabela configuracoes...")
        
        # Criar tabela configuracoes
        cursor.execute("""
            CREATE TABLE configuracoes (
                id INTEGER NOT NULL,
                chave VARCHAR(100) NOT NULL,
                valor TEXT,
                descricao VARCHAR(500),
                tipo VARCHAR(50) DEFAULT 'string',
                data_criacao DATETIME,
                data_atualizacao DATETIME,
                PRIMARY KEY (id),
                UNIQUE (chave)
            )
        """)
        
        conn.commit()
        print("✓ Tabela configuracoes criada com sucesso!")
        
    except Exception as e:
        print(f"✗ Erro ao criar tabela configuracoes: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MIGRAÇÃO ON-PREMISE - TABELAS AUDITORIA E CONFIGURAÇÕES")
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
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("🔄 Reinicie o serviço: sudo supervisorctl restart assessment")
    else:
        print("❌ MIGRAÇÃO CONCLUÍDA COM ERROS")
        sys.exit(1)
    print("=" * 60)