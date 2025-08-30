#!/usr/bin/env python3
"""
Script para corrigir problema de transação PostgreSQL abortada
"""

import sys
import os
sys.path.append('/var/www/assessment')

from app import create_app, db
from sqlalchemy import text

def corrigir_transacao():
    """Corrigir problema de transação PostgreSQL"""
    
    print("🔧 CORRIGINDO TRANSAÇÃO POSTGRESQL")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Fazer rollback de qualquer transação pendente
            print("1. 🔄 Fazendo rollback de transações pendentes...")
            db.session.rollback()
            print("   ✅ Rollback executado")
            
            # 2. Verificar se tabela configuracoes existe
            print("\n2. 📋 Verificando tabela configuracoes...")
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'configuracoes'
            """))
            
            if result.fetchone():
                print("   ✅ Tabela configuracoes existe")
                
                # Verificar se registro logo_sistema existe
                result = db.session.execute(text("""
                    SELECT chave, valor 
                    FROM configuracoes 
                    WHERE chave = 'logo_sistema'
                """))
                
                logo_config = result.fetchone()
                if logo_config:
                    print(f"   ✅ Configuração logo_sistema: {logo_config[1]}")
                else:
                    print("   ⚠️ Configuração logo_sistema não encontrada - criando...")
                    db.session.execute(text("""
                        INSERT INTO configuracoes (chave, valor, descricao, tipo)
                        VALUES ('logo_sistema', '', 'Logo do sistema', 'file')
                    """))
                    db.session.commit()
                    print("   ✅ Configuração logo_sistema criada")
                    
            else:
                print("   ❌ Tabela configuracoes não existe - criando...")
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS configuracoes (
                        id SERIAL PRIMARY KEY,
                        chave VARCHAR(100) UNIQUE NOT NULL,
                        valor TEXT,
                        descricao TEXT,
                        tipo VARCHAR(50) DEFAULT 'text',
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Inserir configuração básica
                db.session.execute(text("""
                    INSERT INTO configuracoes (chave, valor, descricao, tipo)
                    VALUES ('logo_sistema', '', 'Logo do sistema', 'file')
                """))
                
                db.session.commit()
                print("   ✅ Tabela configuracoes criada com configuração básica")
            
            # 3. Verificar coluna forcar_troca_senha
            print("\n3. 👤 Verificando coluna forcar_troca_senha...")
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='respondentes' AND column_name='forcar_troca_senha'
            """))
            
            if result.fetchone():
                print("   ✅ Coluna forcar_troca_senha existe")
            else:
                print("   ⚠️ Adicionando coluna forcar_troca_senha...")
                db.session.execute(text("""
                    ALTER TABLE respondentes 
                    ADD COLUMN forcar_troca_senha BOOLEAN DEFAULT FALSE NOT NULL
                """))
                db.session.commit()
                print("   ✅ Coluna forcar_troca_senha adicionada")
            
            # 4. Fazer commit final
            db.session.commit()
            print("\n✅ CORREÇÃO CONCLUÍDA COM SUCESSO")
            
            # 5. Teste de consulta
            print("\n5. 🧪 TESTE DE CONSULTA:")
            result = db.session.execute(text("""
                SELECT chave, valor FROM configuracoes WHERE chave = 'logo_sistema'
            """))
            config = result.fetchone()
            if config:
                print(f"   ✅ Consulta funcionando: {config[0]} = '{config[1]}'")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante correção: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    corrigir_transacao()