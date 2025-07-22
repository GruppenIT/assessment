#!/usr/bin/env python3
"""
Script final para testar se a correção está funcionando no ambiente on-premise
"""

import os
import sys
from datetime import datetime

def test_final_solution():
    """Teste final da solução"""
    
    print("🔍 Testando solução aplicada...")
    
    try:
        # Importar app que agora tem o env_loader
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
                    # Verificar conexão
                    result = db.session.execute(db.text("SELECT version()")).fetchone()
                    print(f"   ✅ PostgreSQL conectado: {result[0][:50]}...")
                    
                    # Verificar se tabela auditoria existe
                    try:
                        tables_result = db.session.execute(db.text("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'auditoria'
                        """)).fetchone()
                        
                        if tables_result:
                            print("   ✅ Tabela 'auditoria' existe!")
                            
                            # Testar query na tabela auditoria
                            count_result = db.session.execute(db.text("SELECT COUNT(*) FROM auditoria")).fetchone()
                            print(f"   ✅ Tabela auditoria tem {count_result[0]} registros")
                            
                            return "success_complete"
                        else:
                            print("   ⚠️  Tabela 'auditoria' não existe")
                            print("   📝 Execute: python fix_auditoria_postgresql_manual.py")
                            return "success_need_table"
                            
                    except Exception as e:
                        print(f"   ⚠️  Erro ao verificar tabela auditoria: {e}")
                        print("   📝 Execute: python fix_auditoria_postgresql_manual.py")
                        return "success_need_table"
                        
                except Exception as e:
                    print(f"   ✗ Erro na conexão PostgreSQL: {e}")
                    return "postgres_error"
            else:
                print(f"   ❌ Aplicação ainda usando: {database_url}")
                return "still_sqlite"
                
    except Exception as e:
        print(f"   ✗ Erro no teste: {e}")
        return "test_error"

if __name__ == "__main__":
    print("=" * 60)
    print("🏁 TESTE FINAL DA SOLUÇÃO ON-PREMISE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    result = test_final_solution()
    
    print()
    print("=" * 60)
    
    if result == "success_complete":
        print("🎉 SOLUÇÃO COMPLETA!")
        print("✅ PostgreSQL funcionando")
        print("✅ Tabela auditoria criada")
        print("✅ Sistema totalmente operacional")
        
    elif result == "success_need_table":
        print("✅ PostgreSQL funcionando!")
        print("📝 ÚLTIMO PASSO: Criar tabela auditoria")
        print("Execute: python fix_auditoria_postgresql_manual.py")
        
    elif result == "postgres_error":
        print("❌ PostgreSQL conectado mas com erro")
        print("📝 Verifique credenciais e permissões")
        
    elif result == "still_sqlite":
        print("❌ Aplicação ainda usando SQLite")
        print("📝 Problema na configuração do .env")
        
    else:
        print("❌ ERRO NO TESTE")
        print("📝 Investigação adicional necessária")
    
    print("=" * 60)