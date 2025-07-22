#!/usr/bin/env python3
"""
Script para testar se a aplicação está agora conectando no PostgreSQL
"""

import os
import sys

def test_flask_database():
    """Testar configuração do banco na aplicação Flask"""
    
    print("🧪 Testando configuração da aplicação...")
    
    try:
        # Importar configuração da aplicação
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
                    # Tentar query simples
                    result = db.session.execute(db.text("SELECT 1")).fetchone()
                    print("   ✅ Conexão PostgreSQL funcionando!")
                    
                    # Verificar se tabela auditoria existe
                    tables_result = db.session.execute(db.text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'auditoria'
                    """)).fetchone()
                    
                    if tables_result:
                        print("   ✅ Tabela 'auditoria' encontrada!")
                        return True
                    else:
                        print("   ⚠️  Tabela 'auditoria' não existe ainda")
                        print("   📝 Execute: python fix_auditoria_postgresql_manual.py")
                        return False
                        
                except Exception as e:
                    print(f"   ✗ Erro na conexão: {e}")
                    return False
            else:
                print(f"   ❌ Aplicação ainda usando SQLite: {database_url}")
                return False
                
    except Exception as e:
        print(f"   ✗ Erro ao testar aplicação: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE CONEXÃO COM BANCO")
    print("=" * 60)
    
    success = test_flask_database()
    
    print()
    print("=" * 60)
    if success:
        print("✅ BANCO CONFIGURADO CORRETAMENTE")
    else:
        print("❌ AINDA HÁ PROBLEMAS NA CONFIGURAÇÃO")
    print("=" * 60)