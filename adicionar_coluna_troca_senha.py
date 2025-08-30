#!/usr/bin/env python3
"""
Script para adicionar coluna forcar_troca_senha na tabela respondentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def adicionar_coluna_forcar_troca_senha():
    """Adicionar coluna forcar_troca_senha se não existir"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 ADICIONANDO COLUNA FORCAR_TROCA_SENHA")
        print("=" * 45)
        
        try:
            # Verificar se coluna já existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('respondentes')]
            
            if 'forcar_troca_senha' in columns:
                print("✅ Coluna forcar_troca_senha já existe")
                return True
            
            # Adicionar coluna
            sql = "ALTER TABLE respondentes ADD COLUMN forcar_troca_senha BOOLEAN DEFAULT FALSE"
            db.session.execute(text(sql))
            db.session.commit()
            
            print("✅ Coluna forcar_troca_senha adicionada")
            
            # Verificar se foi adicionada
            inspector = inspect(db.engine)
            columns_after = [col['name'] for col in inspector.get_columns('respondentes')]
            
            if 'forcar_troca_senha' in columns_after:
                print("✅ Verificação: coluna disponível")
                
                # Testar inserção de dados
                from models.respondente import Respondente
                resp = Respondente.query.first()
                if resp:
                    resp.forcar_troca_senha = True
                    db.session.commit()
                    
                    resp_test = Respondente.query.get(resp.id)
                    print(f"✅ Teste: {resp_test.forcar_troca_senha}")
                    
                    # Resetar para false
                    resp.forcar_troca_senha = False
                    db.session.commit()
                
                return True
            else:
                print("❌ Coluna não foi adicionada corretamente")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    adicionar_coluna_forcar_troca_senha()