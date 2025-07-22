#!/usr/bin/env python3
"""
Validador de chave OpenAI para identificar problemas específicos
"""

import sys
import json
import env_loader

def validate_key_format(api_key):
    """Validar formato básico da chave"""
    
    issues = []
    
    if not api_key:
        issues.append("Chave está vazia")
        return issues
    
    if not api_key.startswith('sk-'):
        issues.append("Chave deve começar com 'sk-'")
    
    if len(api_key) < 40:
        issues.append(f"Chave muito curta ({len(api_key)} caracteres)")
    
    # Verificar se há caracteres inválidos
    valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    invalid_chars = set(api_key) - valid_chars
    if invalid_chars:
        issues.append(f"Caracteres inválidos: {invalid_chars}")
    
    return issues

def test_key_with_openai(api_key):
    """Testar chave diretamente com OpenAI"""
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Teste mais simples possível
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1
        )
        
        return True, f"Sucesso: {response.choices[0].message.content}"
        
    except Exception as e:
        error_str = str(e)
        
        if "401" in error_str:
            return False, "Chave inválida ou expirada"
        elif "quota" in error_str.lower() or "billing" in error_str.lower():
            return False, "Problema de cobrança/quota excedida"
        elif "rate_limit" in error_str.lower():
            return False, "Limite de taxa excedido"
        else:
            return False, f"Erro: {error_str}"

def check_openai_status():
    """Verificar status da API OpenAI"""
    
    try:
        import urllib.request
        import ssl
        
        # Verificar se consegue acessar o endpoint
        context = ssl.create_default_context()
        req = urllib.request.Request('https://api.openai.com/v1/models')
        req.add_header('Authorization', 'Bearer invalid-key')
        
        try:
            urllib.request.urlopen(req, context=context, timeout=10)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return True, "API OpenAI acessível (erro 401 esperado)"
            else:
                return False, f"API retornou erro {e.code}"
        except Exception as e:
            return False, f"Não conseguiu acessar API: {e}"
            
        return True, "API acessível"
        
    except Exception as e:
        return False, f"Erro ao verificar status: {e}"

def get_key_from_database():
    """Obter chave do banco de dados"""
    
    try:
        from app import create_app
        from models.parametro_sistema import ParametroSistema
        
        app = create_app()
        with app.app_context():
            config = ParametroSistema.get_openai_config()
            return config.get('api_key'), config.get('assistant_name')
            
    except Exception as e:
        return None, f"Erro ao ler banco: {e}"

def main():
    """Função principal"""
    
    print("=" * 60)
    print("🔍 VALIDADOR DE CHAVE OPENAI")
    print("=" * 60)
    
    # 1. Verificar status da API OpenAI
    print("📡 Verificando acesso à API OpenAI...")
    api_ok, api_msg = check_openai_status()
    print(f"   {'✅' if api_ok else '❌'} {api_msg}")
    
    if not api_ok:
        print("\n❌ Não é possível acessar a API OpenAI")
        return 1
    
    print()
    
    # 2. Obter chave do banco
    print("🗄️ Obtendo chave do banco de dados...")
    api_key, assistant_name = get_key_from_database()
    
    if not api_key:
        print(f"❌ {assistant_name}")  # mensagem de erro
        return 1
    
    print(f"✅ Chave obtida: {api_key[:10]}...{api_key[-6:]} ({len(api_key)} chars)")
    print(f"   Assistant: {assistant_name}")
    print()
    
    # 3. Validar formato
    print("🔍 Validando formato da chave...")
    format_issues = validate_key_format(api_key)
    
    if format_issues:
        print("❌ Problemas no formato:")
        for issue in format_issues:
            print(f"   • {issue}")
        return 1
    else:
        print("✅ Formato da chave está correto")
    
    print()
    
    # 4. Testar com OpenAI
    print("🧪 Testando chave com API OpenAI...")
    success, message = test_key_with_openai(api_key)
    
    if success:
        print(f"✅ {message}")
        print("\n🎉 CHAVE VÁLIDA E FUNCIONANDO!")
        
        # Sugestão de próximos passos
        print("\n📋 Próximos passos:")
        print("   1. A chave está funcionando, o problema pode ser temporário")
        print("   2. Tente usar a funcionalidade IA novamente no sistema")
        print("   3. Se ainda der erro, pode ser um problema de rede/proxy")
        
        return 0
    else:
        print(f"❌ {message}")
        
        print("\n🔧 SOLUÇÕES SUGERIDAS:")
        
        if "inválida" in message or "expirada" in message:
            print("   1. Gere uma nova chave em: https://platform.openai.com/api-keys")
            print("   2. Verifique se a chave não expirou")
            print("   3. Confirme se a chave tem permissões adequadas")
        elif "cobrança" in message or "quota" in message:
            print("   1. Verifique seu saldo em: https://platform.openai.com/usage")
            print("   2. Configure método de pagamento se necessário")
            print("   3. Verifique limites de uso da sua conta")
        else:
            print("   1. Verifique conectividade com api.openai.com")
            print("   2. Confirme se não há proxy/firewall bloqueando")
        
        print(f"\n   Para reconfigurar no sistema:")
        print(f"   • Acesse: Configurações > Parâmetros do Sistema")
        print(f"   • Seção: Integração ChatGPT")
        print(f"   • Cole uma nova chave válida")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())