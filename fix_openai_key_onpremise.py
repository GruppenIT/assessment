#!/usr/bin/env python3
"""
Script para corrigir problemas com chave OpenAI no ambiente on-premise
"""

import os
import sys
from datetime import datetime

# Carregar variáveis de ambiente
import env_loader

def limpar_chave_openai():
    """Remover chave OpenAI atual para reconfigurar"""
    
    print("🧹 Limpando configuração OpenAI atual...")
    
    try:
        from app import create_app, db
        from models.parametro_sistema import ParametroSistema
        
        app = create_app()
        
        with app.app_context():
            # Remover parâmetros OpenAI
            params_to_delete = ['openai_api_key', 'openai_assistant_name']
            
            for param_name in params_to_delete:
                param = ParametroSistema.query.filter_by(chave=param_name).first()
                if param:
                    db.session.delete(param)
                    print(f"✅ Removido parâmetro: {param_name}")
                else:
                    print(f"⚠️ Parâmetro não encontrado: {param_name}")
            
            db.session.commit()
            print("✅ Configuração OpenAI limpa")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao limpar configuração: {e}")
        return False

def reconfigurar_chave_openai():
    """Reconfigurar chave OpenAI com input do usuário"""
    
    print("🔧 Reconfigurando OpenAI...")
    print("📝 Cole sua chave OpenAI aqui (deve começar com sk-)")
    print("💡 Você pode obter uma em: https://platform.openai.com/api-keys")
    print()
    
    api_key = input("Chave OpenAI: ").strip()
    
    # Validações básicas
    if not api_key:
        print("❌ Chave não pode estar vazia")
        return False
    
    if not api_key.startswith('sk-'):
        print("❌ Chave deve começar com 'sk-'")
        return False
    
    if len(api_key) < 40:
        print("❌ Chave muito curta")
        return False
    
    # Nome do assistente
    assistant_name = input("Nome do Assistant (opcional, pressione Enter para padrão): ").strip()
    if not assistant_name:
        assistant_name = "Assessment Assistant"
    
    try:
        from app import create_app, db
        from models.parametro_sistema import ParametroSistema
        
        app = create_app()
        
        with app.app_context():
            # Configurar OpenAI
            ParametroSistema.set_openai_config(api_key, assistant_name)
            
            print("✅ Configuração OpenAI salva no banco")
            
            # Verificar se foi salva corretamente
            config = ParametroSistema.get_openai_config()
            if config.get('api_key_configured'):
                print("✅ Verificação: chave carregada corretamente")
                retrieved_key = config.get('api_key')
                if retrieved_key == api_key:
                    print("✅ Verificação: chave matches")
                else:
                    print("⚠️ Verificação: chave não matches")
            else:
                print("❌ Verificação: chave não foi configurada")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao salvar configuração: {e}")
        return False

def testar_chave_openai():
    """Testar se a chave OpenAI funciona"""
    
    print("🧪 Testando chave OpenAI...")
    
    try:
        from utils.openai_utils import OpenAIAssistant
        
        assistant = OpenAIAssistant()
        
        if not assistant.is_configured():
            print("❌ Assistant não configurado")
            return False
        
        # Teste simples
        response = assistant.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Responda apenas: TESTE OK"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API OpenAI respondeu: '{result}'")
        
        if "TESTE OK" in result or "OK" in result:
            print("✅ Teste bem-sucedido!")
            return True
        else:
            print("⚠️ Resposta inesperada, mas API funcionou")
            return True
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        
        # Análise do erro
        if "401" in str(e) or "Unauthorized" in str(e):
            print("🔍 Análise: Chave API inválida, expirada ou incorreta")
        elif "403" in str(e) or "Forbidden" in str(e):
            print("🔍 Análise: Conta sem permissão para usar a API")
        elif "quota" in str(e).lower() or "billing" in str(e).lower():
            print("🔍 Análise: Problema de cobrança ou limite excedido")
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            print("🔍 Análise: Problema de conectividade")
        else:
            print("🔍 Análise: Erro desconhecido")
        
        return False

def main():
    """Função principal"""
    
    print("=" * 60)
    print("🔧 CORREÇÃO DA CHAVE OPENAI ON-PREMISE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    print("Este script vai:")
    print("1. Limpar configuração OpenAI atual")
    print("2. Reconfigurar com nova chave")
    print("3. Testar a configuração")
    print()
    
    resposta = input("Continuar? (s/N): ").lower().strip()
    if resposta != 's':
        print("Operação cancelada")
        return 1
    
    print()
    
    # Passo 1: Limpar
    if not limpar_chave_openai():
        print("Erro ao limpar configuração")
        return 1
    
    print()
    
    # Passo 2: Reconfigurar
    if not reconfigurar_chave_openai():
        print("Erro ao reconfigurar")
        return 1
    
    print()
    
    # Passo 3: Testar
    if testar_chave_openai():
        print()
        print("=" * 60)
        print("🎉 CONFIGURAÇÃO OPENAI CORRIGIDA!")
        print("=" * 60)
        print("✅ Chave configurada e testada com sucesso")
        print("🌐 Agora você pode usar os recursos de IA no sistema")
        print("=" * 60)
        return 0
    else:
        print()
        print("=" * 60)
        print("❌ CONFIGURAÇÃO SALVA MAS TESTE FALHOU")
        print("=" * 60)
        print("📝 Verifique se:")
        print("   - A chave está correta")
        print("   - A conta OpenAI está ativa")  
        print("   - Há créditos/billing configurado")
        print("   - Não há problemas de rede")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())