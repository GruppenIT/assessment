#!/usr/bin/env python3
"""
Script para debugar problemas com OpenAI API no ambiente on-premise
"""

import os
import sys
from datetime import datetime

# Carregar variáveis de ambiente
import env_loader

def debug_parametro_sistema():
    """Debug do sistema de parâmetros"""
    
    print("🔍 Debugando sistema de parâmetros...")
    
    try:
        from app import create_app, db
        from models.parametro_sistema import ParametroSistema
        
        app = create_app()
        
        with app.app_context():
            # Verificar se parâmetro existe
            param = ParametroSistema.query.filter_by(chave='openai_api_key').first()
            
            if param:
                print("✅ Parâmetro 'openai_api_key' encontrado no banco")
                print(f"   Tipo: {param.tipo}")
                print(f"   Tem valor criptografado: {bool(param.valor_criptografado)}")
                print(f"   Tem valor normal: {bool(param.valor)}")
                print(f"   Data atualização: {param.data_atualizacao}")
                
                # Tentar descriptografar
                try:
                    valor = ParametroSistema.get_valor('openai_api_key')
                    if valor:
                        print(f"   Valor descriptografado: {valor[:10]}...{valor[-6:]} (tamanho: {len(valor)})")
                        
                        # Verificar formato da chave
                        if valor.startswith('sk-'):
                            print("   ✅ Chave tem formato correto (sk-)")
                        else:
                            print("   ❌ Chave NÃO tem formato correto (deve começar com sk-)")
                            
                        # Verificar tamanho esperado
                        if len(valor) >= 40:
                            print("   ✅ Chave tem tamanho adequado")
                        else:
                            print("   ❌ Chave muito curta")
                            
                    else:
                        print("   ❌ Valor descriptografado é None/vazio")
                        
                except Exception as e:
                    print(f"   ❌ Erro ao descriptografar: {e}")
                    
            else:
                print("❌ Parâmetro 'openai_api_key' NÃO encontrado no banco")
                
                # Listar todos os parâmetros para debug
                params = ParametroSistema.query.all()
                print(f"📋 Parâmetros existentes ({len(params)}):")
                for p in params:
                    print(f"   - {p.chave} ({p.tipo})")
            
            return param is not None
            
    except Exception as e:
        print(f"❌ Erro ao debugar parâmetros: {e}")
        return False

def debug_criptografia():
    """Debug do sistema de criptografia"""
    
    print("🔐 Debugando sistema de criptografia...")
    
    try:
        from app import create_app
        from models.parametro_sistema import ParametroSistema
        from cryptography.fernet import Fernet
        
        app = create_app()
        with app.app_context():
            # Verificar chave de criptografia
            chave = ParametroSistema.get_chave_criptografia()
            print(f"✅ Chave de criptografia obtida (tamanho: {len(chave)} bytes)")
            
            # Testar criptografia
            teste_valor = "sk-test123456789"
            fernet = Fernet(chave)
            
            # Criptografar
            valor_criptografado = fernet.encrypt(teste_valor.encode())
            print("✅ Teste de criptografia funcionou")
            
            # Descriptografar
            valor_descriptografado = fernet.decrypt(valor_criptografado).decode()
            if valor_descriptografado == teste_valor:
                print("✅ Teste de descriptografia funcionou")
            else:
                print("❌ Erro na descriptografia")
                
            return True
        
    except Exception as e:
        print(f"❌ Erro no sistema de criptografia: {e}")
        return False

def debug_openai_config():
    """Debug da configuração OpenAI"""
    
    print("🤖 Debugando configuração OpenAI...")
    
    try:
        from app import create_app
        from models.parametro_sistema import ParametroSistema
        
        app = create_app()
        with app.app_context():
            config = ParametroSistema.get_openai_config()
            
            print(f"📋 Configuração OpenAI:")
            print(f"   API Key configurada: {config.get('api_key_configured')}")
            print(f"   Assistant name: {config.get('assistant_name')}")
            
            api_key = config.get('api_key')
            if api_key:
                print(f"   API Key: {api_key[:10]}...{api_key[-6:]} (tamanho: {len(api_key)})")
                
                # Validações básicas
                if api_key.startswith('sk-'):
                    print("   ✅ Formato da chave correto")
                else:
                    print("   ❌ Formato da chave incorreto")
                    
                if len(api_key) >= 40:
                    print("   ✅ Tamanho da chave adequado")  
                else:
                    print("   ❌ Tamanho da chave inadequado")
                    
            else:
                print("   ❌ API Key não encontrada")
                
            return bool(api_key)
        
    except Exception as e:
        print(f"❌ Erro ao verificar configuração OpenAI: {e}")
        return False

def debug_openai_client():
    """Debug do cliente OpenAI"""
    
    print("🔗 Debugando cliente OpenAI...")
    
    try:
        from app import create_app
        from utils.openai_utils import OpenAIAssistant
        
        app = create_app()
        with app.app_context():
            assistant = OpenAIAssistant()
            
            if assistant.is_configured():
                print("✅ OpenAI Assistant configurado")
                print(f"   Assistant name: {assistant.assistant_name}")
                
                # Testar chamada simples
                print("🧪 Testando chamada à API OpenAI...")
                
                try:
                    response = assistant.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "user", "content": "Responda apenas: OK"}
                        ],
                        max_tokens=5
                    )
                    
                    resultado = response.choices[0].message.content.strip()
                    print(f"   ✅ API respondeu: '{resultado}'")
                    return True
                    
                except Exception as e:
                    print(f"   ❌ Erro na chamada da API: {e}")
                    
                    # Verificar se é erro 401
                    if "401" in str(e) or "Unauthorized" in str(e):
                        print("   🔍 Erro 401: Chave API inválida ou expirada")
                    elif "quota" in str(e).lower():
                        print("   🔍 Erro de quota: Limite da API excedido")
                    elif "network" in str(e).lower() or "connection" in str(e).lower():
                        print("   🔍 Erro de rede: Problema de conectividade")
                    else:
                        print("   🔍 Erro desconhecido")
                        
                    return False
            else:
                print("❌ OpenAI Assistant NÃO configurado")
                return False
            
    except Exception as e:
        print(f"❌ Erro ao debugar cliente OpenAI: {e}")
        return False

def debug_variaveis_ambiente():
    """Debug das variáveis de ambiente"""
    
    print("🌍 Debugando variáveis de ambiente...")
    
    openai_env = os.environ.get('OPENAI_API_KEY')
    if openai_env:
        print(f"✅ OPENAI_API_KEY encontrada no ambiente: {openai_env[:10]}...{openai_env[-6:]}")
    else:
        print("⚠️ OPENAI_API_KEY não encontrada no ambiente")
        
    # Outras variáveis relacionadas
    other_vars = ['DATABASE_URL', 'SESSION_SECRET', 'CRYPTO_KEY']
    for var in other_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: configurada")
        else:
            print(f"⚠️ {var}: não configurada")

def main():
    """Função principal de debug"""
    
    print("=" * 60)
    print("🔍 DEBUG OPENAI ON-PREMISE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Lista de verificações
    verificacoes = [
        ("Variáveis de ambiente", debug_variaveis_ambiente),
        ("Sistema de criptografia", debug_criptografia),
        ("Sistema de parâmetros", debug_parametro_sistema),
        ("Configuração OpenAI", debug_openai_config),
        ("Cliente OpenAI", debug_openai_client)
    ]
    
    resultados = []
    
    for nome, funcao in verificacoes:
        print(f"📋 {nome}...")
        try:
            resultado = funcao()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ Erro inesperado em {nome}: {e}")
            resultados.append((nome, False))
        print()
    
    # Relatório final
    print("=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    
    checks_ok = sum(1 for _, result in resultados if result)
    total_checks = len(resultados)
    
    print(f"✅ Verificações OK: {checks_ok}/{total_checks}")
    
    for nome, sucesso in resultados:
        status = "✅" if sucesso else "❌"
        print(f"   {status} {nome}")
    
    if checks_ok == total_checks:
        print("\n🎉 TUDO FUNCIONANDO!")
    else:
        print("\n🔧 PROBLEMAS IDENTIFICADOS:")
        
        if not resultados[2][1]:  # Sistema de parâmetros
            print("   📝 Verificar se chave foi salva corretamente nos parâmetros")
        
        if not resultados[4][1]:  # Cliente OpenAI
            print("   📝 Verificar se a chave OpenAI é válida e ativa")
            print("   📝 Testar a chave em: https://platform.openai.com/playground")
    
    print("=" * 60)
    
    return checks_ok == total_checks

if __name__ == "__main__":
    sys.exit(0 if main() else 1)