#!/usr/bin/env python3
"""
Script para debugar problemas de login com senhas especiais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.usuario import Usuario
from models.respondente import Respondente
from werkzeug.security import check_password_hash, generate_password_hash

def debug_password_issues():
    """Debug de problemas de senha"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 INVESTIGANDO PROBLEMAS DE SENHA COM @")
        print("=" * 50)
        
        # Buscar usuários
        admin = Usuario.query.filter_by(email='admin@sistema.com').first()
        if admin:
            print(f"\n👤 Admin encontrado: {admin.email}")
            print(f"   Hash atual: {admin.senha_hash[:50]}...")
            
            # Testar senhas problemáticas
            senhas_teste = [
                "P@ssw0rd@.!",
                "j93JF#+;NCE]q@D", 
                "System01!.",
                "admin123"
            ]
            
            print("\n🧪 Testando senhas:")
            for senha in senhas_teste:
                resultado = check_password_hash(admin.senha_hash, senha)
                print(f"   '{senha}' -> {'✅ OK' if resultado else '❌ FALHOU'}")
            
            # Testar com diferentes encodings
            print("\n🔤 Testando encodings:")
            senha_problema = "P@ssw0rd@.!"
            
            # Teste 1: UTF-8
            try:
                senha_utf8 = senha_problema.encode('utf-8').decode('utf-8')
                resultado = check_password_hash(admin.senha_hash, senha_utf8)
                print(f"   UTF-8: {'✅ OK' if resultado else '❌ FALHOU'}")
            except Exception as e:
                print(f"   UTF-8: ❌ ERRO - {e}")
            
            # Teste 2: Latin1
            try:
                senha_latin1 = senha_problema.encode('latin1').decode('latin1')
                resultado = check_password_hash(admin.senha_hash, senha_latin1)
                print(f"   Latin1: {'✅ OK' if resultado else '❌ FALHOU'}")
            except Exception as e:
                print(f"   Latin1: ❌ ERRO - {e}")
            
            # Teste 3: Escape de caracteres especiais
            try:
                import urllib.parse
                senha_encoded = urllib.parse.unquote(senha_problema)
                resultado = check_password_hash(admin.senha_hash, senha_encoded)
                print(f"   URL decode: {'✅ OK' if resultado else '❌ FALHOU'}")
            except Exception as e:
                print(f"   URL decode: ❌ ERRO - {e}")
        
        print("\n" + "=" * 50)
        print("💡 SOLUÇÃO: Vamos aplicar normalização na verificação de senha")

def create_test_user_with_special_password():
    """Criar usuário de teste com senha especial"""
    app = create_app()
    
    with app.app_context():
        # Verificar se usuário teste já existe
        teste_user = Usuario.query.filter_by(email='teste@special.com').first()
        if teste_user:
            db.session.delete(teste_user)
            db.session.commit()
        
        # Criar novo usuário com senha especial
        senha_especial = "P@ssw0rd@.!"
        hash_senha = generate_password_hash(senha_especial)
        
        novo_user = Usuario(
            nome="Teste Especial",
            email="teste@special.com",
            senha_hash=hash_senha,
            tipo="admin",
            ativo=True
        )
        
        db.session.add(novo_user)
        db.session.commit()
        
        print(f"✅ Usuário teste criado: teste@special.com")
        print(f"   Senha: {senha_especial}")
        print(f"   Hash: {hash_senha[:50]}...")
        
        # Verificar imediatamente
        resultado = check_password_hash(hash_senha, senha_especial)
        print(f"   Verificação: {'✅ OK' if resultado else '❌ FALHOU'}")

if __name__ == "__main__":
    debug_password_issues()
    print()
    create_test_user_with_special_password()