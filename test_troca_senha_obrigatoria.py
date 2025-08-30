#!/usr/bin/env python3
"""
Teste da funcionalidade de troca obrigatória de senha
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.respondente import Respondente

def test_troca_senha_obrigatoria():
    """Testar funcionalidade de troca obrigatória de senha"""
    
    app = create_app()
    
    with app.app_context():
        print("🔑 TESTE TROCA OBRIGATÓRIA DE SENHA")
        print("=" * 45)
        
        # 1. Verificar se campo existe
        resp = Respondente.query.first()
        if not resp:
            print("❌ Nenhum respondente encontrado")
            return
            
        print(f"📋 Testando com: {resp.nome}")
        
        # 2. Verificar se campo existe
        if hasattr(resp, 'forcar_troca_senha'):
            print("✅ Campo forcar_troca_senha disponível")
            print(f"   Status atual: {resp.forcar_troca_senha}")
        else:
            print("❌ Campo forcar_troca_senha não encontrado")
            return
        
        # 3. Testar ativação da flag
        print("\n🔧 ATIVANDO TROCA OBRIGATÓRIA")
        resp.forcar_troca_senha = True
        db.session.commit()
        print("✅ Flag ativada")
        
        # 4. Verificar se foi salva
        resp_updated = Respondente.query.get(resp.id)
        print(f"   Status após salvar: {resp_updated.forcar_troca_senha}")
        
        # 5. Simular troca de senha
        print("\n🔄 SIMULANDO TROCA DE SENHA")
        senha_anterior = resp_updated.senha_hash
        resp_updated.set_password('nova_senha_teste_123')
        resp_updated.forcar_troca_senha = False
        db.session.commit()
        
        senha_nova = resp_updated.senha_hash
        print(f"✅ Senha alterada: {'✅' if senha_anterior != senha_nova else '❌'}")
        print(f"✅ Flag desmarcada: {'✅' if not resp_updated.forcar_troca_senha else '❌'}")
        
        # 6. Testar verificação de senha
        print("\n🔍 TESTANDO VERIFICAÇÃO")
        verifica_nova = resp_updated.check_password('nova_senha_teste_123')
        print(f"✅ Nova senha funciona: {'✅' if verifica_nova else '❌'}")
        
        print("\n" + "=" * 45)
        print("🎉 TESTE CONCLUÍDO")
        
        return True

if __name__ == "__main__":
    test_troca_senha_obrigatoria()