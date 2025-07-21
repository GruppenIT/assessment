#!/usr/bin/env python3
"""
Script para criar a tabela de auditoria no ambiente on-premise
Execute este script após fazer o deploy para criar as tabelas necessárias
"""

import os
import sys
import sqlite3
from datetime import datetime

def create_auditoria_table():
    """Criar tabela de auditoria no SQLite"""
    
    # Determinar o caminho do banco de dados
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
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
            return
        
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
        
    except Exception as e:
        print(f"✗ Erro ao criar tabela auditoria: {e}")
        return False
    finally:
        conn.close()
    
    return True

def create_configuracoes_table():
    """Criar tabela de configurações se não existir"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
    
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
            return
        
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
    print("🔄 Iniciando migração das tabelas...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    if not create_auditoria_table():
        success = False
    
    if not create_configuracoes_table():
        success = False
    
    print()
    if success:
        print("✅ Migração concluída com sucesso!")
    else:
        print("❌ Migração concluída com erros")
        sys.exit(1)