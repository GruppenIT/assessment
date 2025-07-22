#!/usr/bin/env python3
"""
Teste simples da API OpenAI usando a configuração existente no banco
"""

import sys
import env_loader

def test_openai_from_db():
    """Testar OpenAI usando configuração salva no banco"""
    
    print("🧪 Testando OpenAI com configuração do banco...")
    
    try:
        from app import create_app
        from utils.openai_utils import OpenAIAssistant
        
        app = create_app()
        
        with app.app_context():
            print("📋 Inicializando OpenAI Assistant...")
            assistant = OpenAIAssistant()
            
            if not assistant.is_configured():
                print("❌ Assistant não configurado")
                return False
            
            print(f"✅ Assistant configurado: {assistant.assistant_name}")
            
            # Teste básico
            print("🚀 Fazendo chamada de teste...")
            
            response = assistant.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": "Responda apenas com: TESTE FUNCIONOU"}
                ],
                max_tokens=10,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Resposta da API: '{result}'")
            
            # Teste de função real do sistema
            print("🧪 Testando função de introdução...")
            
            projeto_data = {
                "projeto": {"nome": "Teste"},
                "cliente": {"razao_social": "Empresa Teste"},
                "assessment": {"nome": "Cibersegurança"},
                "respondentes": [{"nome": "Teste", "email": "test@test.com"}],
                "periodo": {"inicio": "2024-01-01", "fim": "2024-01-31"}
            }
            
            introducao = assistant.gerar_introducao_projeto(projeto_data)
            
            if introducao:
                print("✅ Função de introdução funcionou!")
                print(f"📝 Introdução gerada ({len(introducao)} caracteres):")
                print(f"   {introducao[:100]}...")
                return True
            else:
                print("❌ Função de introdução falhou")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        
        # Análise do erro
        error_str = str(e)
        if "401" in error_str:
            print("🔍 Análise: Erro 401 - Chave API inválida")
            print("   Verifique se a chave no banco está correta")
            print("   Teste a chave em: https://platform.openai.com/playground")
        elif "quota" in error_str.lower():
            print("🔍 Análise: Erro de quota/billing")
            print("   Verifique seu saldo OpenAI")
        elif "network" in error_str.lower():
            print("🔍 Análise: Erro de rede")
            print("   Verifique conectividade com api.openai.com")
        else:
            print("🔍 Análise: Erro inesperado")
        
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE SIMPLES OPENAI")
    print("=" * 60)
    
    if test_openai_from_db():
        print("\n🎉 TESTE PASSOU! OpenAI está funcionando.")
        sys.exit(0)
    else:
        print("\n❌ TESTE FALHOU! Verifique a configuração.")
        sys.exit(1)