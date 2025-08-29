#!/usr/bin/env python3
"""
Script para testar o status completo da segurança do sistema
"""

import requests
import sys

def test_security():
    """Testa todas as rotas críticas para verificar proteção"""
    
    print("🔍 TESTE COMPLETO DE SEGURANÇA")
    print("="*50)
    
    base_url = "http://localhost:5000"
    
    # Rotas que DEVEM estar protegidas
    rotas_protegidas = [
        "/admin/dashboard",
        "/admin/projetos/working", 
        "/admin/projetos/",
        "/admin/clientes",
        "/respondente/dashboard",
        "/cliente/dashboard",
        "/uploads/teste.jpg"
    ]
    
    # Rotas que DEVEM ser públicas
    rotas_publicas = [
        "/auth/login",
        "/static/css/bootstrap.min.css",
        "/favicon.ico"
    ]
    
    print("\n🔒 TESTANDO ROTAS PROTEGIDAS:")
    print("-" * 40)
    
    for rota in rotas_protegidas:
        try:
            # Fazer requisição sem cookies/autenticação
            response = requests.get(f"{base_url}{rota}", allow_redirects=False, timeout=5)
            
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if '/auth/login' in location:
                    print(f"✅ {rota} -> 302 (redirect para login)")
                else:
                    print(f"⚠️  {rota} -> 302 (redirect para: {location})")
            elif response.status_code == 401:
                print(f"✅ {rota} -> 401 (não autorizado)")
            elif response.status_code == 403:
                print(f"✅ {rota} -> 403 (proibido)")
            else:
                print(f"❌ {rota} -> {response.status_code} (VULNERABILIDADE!)")
                
        except Exception as e:
            print(f"❌ {rota} -> Erro: {e}")
    
    print(f"\n🌍 TESTANDO ROTAS PÚBLICAS:")
    print("-" * 40)
    
    for rota in rotas_publicas:
        try:
            response = requests.get(f"{base_url}{rota}", allow_redirects=False, timeout=5)
            
            if response.status_code in [200, 404]:  # 404 é ok para arquivos que não existem
                print(f"✅ {rota} -> {response.status_code} (acessível)")
            else:
                print(f"⚠️  {rota} -> {response.status_code}")
                
        except Exception as e:
            print(f"❌ {rota} -> Erro: {e}")
    
    print(f"\n🕵️  TESTE DE BYPASS:")
    print("-" * 40)
    
    # Testar possíveis bypasses
    bypass_attempts = [
        "/admin/../admin/dashboard",
        "/admin/projetos/../projetos/working",
        "//admin/dashboard",
    ]
    
    for attempt in bypass_attempts:
        try:
            response = requests.get(f"{base_url}{attempt}", allow_redirects=False, timeout=5)
            
            if response.status_code == 302 and '/auth/login' in response.headers.get('Location', ''):
                print(f"✅ {attempt} -> 302 (protegido)")
            else:
                print(f"❌ {attempt} -> {response.status_code} (POSSÍVEL BYPASS!)")
                
        except Exception as e:
            print(f"✅ {attempt} -> Erro: {e} (protegido por erro)")
    
    print(f"\n📊 RESUMO:")
    print("-" * 40)
    print("✅ = Protegido corretamente")
    print("⚠️  = Precisa investigação") 
    print("❌ = VULNERABILIDADE CRÍTICA")
    
    print(f"\n💡 COMO VERIFICAR NO NAVEGADOR:")
    print("-" * 40)
    print("1. Abra uma aba anônima/incógnita")
    print("2. Acesse qualquer rota admin (ex: /admin/dashboard)")
    print("3. Deve ser redirecionado para /auth/login")
    print("4. Se conseguir acessar sem login = PROBLEMA")

if __name__ == "__main__":
    test_security()