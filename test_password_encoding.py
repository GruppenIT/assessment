#!/usr/bin/env python3
"""
Script para testar problemas de encoding de senha com caracteres especiais
"""

from werkzeug.security import generate_password_hash, check_password_hash

def test_passwords():
    """Testa diferentes senhas com caracteres especiais"""
    
    test_passwords = [
        "P@ssw0rd@.!",
        "j93JF#+;NCE]q@D",
        "System01!.",
        "senha123",
        "test@123",
        "admin@sistema.com"
    ]
    
    print("🧪 TESTE DE ENCODING DE SENHAS")
    print("=" * 50)
    
    for senha in test_passwords:
        print(f"\n📝 Testando senha: '{senha}'")
        
        # Gerar hash
        try:
            hash_senha = generate_password_hash(senha)
            print(f"✅ Hash gerado: {hash_senha[:50]}...")
            
            # Verificar hash
            if check_password_hash(hash_senha, senha):
                print("✅ Verificação: OK")
            else:
                print("❌ Verificação: FALHOU")
                
            # Testar com encoding UTF-8 explícito
            senha_utf8 = senha.encode('utf-8').decode('utf-8')
            if check_password_hash(hash_senha, senha_utf8):
                print("✅ Verificação UTF-8: OK")
            else:
                print("❌ Verificação UTF-8: FALHOU")
                
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_passwords()