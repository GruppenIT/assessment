#!/usr/bin/env python3
"""
Testar a correção de senhas com caracteres especiais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.usuario import Usuario
from utils.password_utils import safe_check_password_hash, safe_generate_password_hash

def test_password_fix():
    """Testar correção de senhas"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 TESTE DA CORREÇÃO DE SENHAS")
        print("=" * 50)
        
        # Testar com usuário teste que criamos
        teste_user = Usuario.query.filter_by(email='teste@special.com').first()
        if teste_user:
            senhas_teste = [
                "P@ssw0rd@.!",
                "j93JF#+;NCE]q@D", 
                "System01!."
            ]
            
            print(f"👤 Testando usuário: {teste_user.email}")
            
            for senha in senhas_teste:
                resultado = safe_check_password_hash(teste_user.senha_hash, senha)
                print(f"   '{senha}' -> {'✅ OK' if resultado else '❌ FALHOU'}")
        
        print("\n🔧 CRIANDO USUÁRIO COM SENHA ESPECIAL")
        
        # Criar usuário com senha problemática
        senha_especial = "P@ssw0rd@.!"
        hash_seguro = safe_generate_password_hash(senha_especial)
        
        # Verificar se usuário já existe
        user_especial = Usuario.query.filter_by(email='admin@special.com').first()
        if user_especial:
            db.session.delete(user_especial)
            db.session.commit()
        
        # Criar novo usuário
        novo_user = Usuario(
            nome="Admin Especial",
            email="admin@special.com", 
            senha_hash=hash_seguro,
            tipo="admin",
            ativo=True
        )
        
        db.session.add(novo_user)
        db.session.commit()
        
        print(f"✅ Usuário criado: admin@special.com")
        print(f"   Senha: {senha_especial}")
        
        # Testar verificação
        resultado = safe_check_password_hash(hash_seguro, senha_especial)
        print(f"   Verificação: {'✅ OK' if resultado else '❌ FALHOU'}")
        
        print("\n" + "=" * 50)
        print("💡 TESTE DE LOGIN COM DIFERENTES SENHAS:")
        
        senhas_problematicas = [
            "P@ssw0rd@.!",
            "j93JF#+;NCE]q@D",
            "test@domain.com",
            "senha#123!@",
            "System01!."
        ]
        
        for senha in senhas_problematicas:
            # Criar hash
            hash_senha = safe_generate_password_hash(senha)
            
            # Verificar
            resultado = safe_check_password_hash(hash_senha, senha)
            print(f"   '{senha}' -> {'✅ OK' if resultado else '❌ FALHOU'}")

if __name__ == "__main__":
    test_password_fix()