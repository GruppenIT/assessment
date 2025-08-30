#!/usr/bin/env python3
"""
Script para inicializar tabela de 2FA no banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.two_factor import TwoFactor

def init_2fa_table():
    """Inicializar tabela de 2FA"""
    
    app = create_app()
    
    with app.app_context():
        print("🔐 INICIALIZANDO TABELA DE 2FA")
        print("=" * 40)
        
        try:
            # Criar todas as tabelas (incluindo two_factor)
            db.create_all()
            print("✅ Tabela two_factor criada/verificada")
            
            # Verificar se tabela foi criada
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'two_factor' in tables:
                print("✅ Tabela two_factor disponível no banco")
                
                # Mostrar colunas
                columns = inspector.get_columns('two_factor')
                print("\n📋 Colunas da tabela:")
                for col in columns:
                    print(f"   • {col['name']} ({col['type']})")
            else:
                print("❌ Tabela two_factor não foi criada")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
        
        print("\n" + "=" * 40)
        print("🎉 INICIALIZAÇÃO CONCLUÍDA")
        return True

if __name__ == "__main__":
    init_2fa_table()