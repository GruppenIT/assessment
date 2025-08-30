#!/usr/bin/env python3
"""
Script para testar fluxo de troca obrigatória de senha
"""

import sys
import os
sys.path.append('/var/www/assessment')

from app import create_app, db
from models.respondente import Respondente

def testar_fluxo():
    """Testar e configurar fluxo de troca obrigatória"""
    
    print("🧪 TESTANDO FLUXO DE TROCA OBRIGATÓRIA")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar respondente para teste
            respondente = Respondente.query.first()
            
            if not respondente:
                print("❌ Nenhum respondente encontrado")
                return False
            
            print(f"📊 Respondente: {respondente.nome}")
            print(f"📧 Email: {respondente.email}")
            print(f"🔑 Login: {respondente.login}")
            print(f"🔒 Forçar troca: {respondente.forcar_troca_senha}")
            
            # Se não está marcado, marcar para teste
            if not respondente.forcar_troca_senha:
                respondente.forcar_troca_senha = True
                db.session.commit()
                print("✅ Marcado para troca obrigatória")
            
            print("\n📋 INSTRUÇÕES DE TESTE:")
            print(f"1. Faça login com: {respondente.login}")
            print("2. Use a senha atual do respondente")
            print("3. Sistema deve mostrar 'Login realizado com sucesso!'")
            print("4. Deve redirecionar para página de troca de senha")
            print("5. Após trocar, deve acessar o dashboard normalmente")
            
            print(f"\n🔗 URL de teste: https://assessments.zerobox.com.br/auth/login")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

if __name__ == "__main__":
    testar_fluxo()