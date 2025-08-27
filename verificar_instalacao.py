#!/usr/bin/env python3
"""
Script para verificar se a instalação está funcionando corretamente
"""

import os
import sys
import subprocess
import requests
import time

def verificar_supervisor():
    """Verifica se o Supervisor está funcionando"""
    try:
        result = subprocess.run(['sudo', 'supervisorctl', 'status', 'assessment'], 
                              capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            print("✅ Supervisor: assessment está RUNNING")
            return True
        else:
            print(f"❌ Supervisor: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar Supervisor: {e}")
        return False

def verificar_web():
    """Verifica se a aplicação web está respondendo"""
    try:
        response = requests.get('http://localhost:8000', timeout=10)
        if response.status_code == 200:
            print("✅ Web: Aplicação respondendo na porta 8000")
            return True
        else:
            print(f"❌ Web: Status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Web: Não é possível conectar na porta 8000")
        return False
    except Exception as e:
        print(f"❌ Web: Erro {e}")
        return False

def verificar_logs():
    """Verifica se há erros nos logs"""
    try:
        # Últimas 20 linhas do log
        result = subprocess.run(['sudo', 'tail', '-n', '20', '/var/log/assessment.log'], 
                              capture_output=True, text=True)
        
        logs = result.stdout
        
        # Verificar por erros críticos
        erros_criticos = ['ERROR', 'CRITICAL', 'FATAL', 'Exception', 'Traceback']
        erros_encontrados = []
        
        for linha in logs.split('\n'):
            for erro in erros_criticos:
                if erro in linha:
                    erros_encontrados.append(linha.strip())
        
        if erros_encontrados:
            print("⚠️  Logs: Erros encontrados:")
            for erro in erros_encontrados[:3]:  # Máximo 3 erros
                print(f"   {erro}")
        else:
            print("✅ Logs: Sem erros críticos nas últimas 20 linhas")
            
        return len(erros_encontrados) == 0
        
    except Exception as e:
        print(f"❌ Erro ao verificar logs: {e}")
        return False

def verificar_banco():
    """Verifica se o banco está acessível"""
    try:
        # Verificar se PostgreSQL está rodando
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'postgresql'], 
                              capture_output=True, text=True)
        
        if 'active' in result.stdout:
            print("✅ PostgreSQL: Serviço ativo")
            return True
        else:
            print(f"❌ PostgreSQL: {result.stdout.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar PostgreSQL: {e}")
        return False

def main():
    """Executa todas as verificações"""
    
    print("🔍 VERIFICAÇÃO COMPLETA DA INSTALAÇÃO")
    print("="*50)
    
    verificacoes = [
        ("Banco de Dados", verificar_banco),
        ("Supervisor", verificar_supervisor),
        ("Logs", verificar_logs),
        ("Aplicação Web", verificar_web),
    ]
    
    resultados = []
    
    for nome, funcao in verificacoes:
        print(f"\n📋 Verificando {nome}...")
        resultado = funcao()
        resultados.append((nome, resultado))
        
        if not resultado and nome == "Aplicação Web":
            print("   ⏳ Aguardando 5 segundos e tentando novamente...")
            time.sleep(5)
            resultado = funcao()
            resultados[-1] = (nome, resultado)
    
    print(f"\n🎯 RESUMO DA VERIFICAÇÃO")
    print("="*30)
    
    total_ok = 0
    for nome, ok in resultados:
        status = "✅" if ok else "❌"
        print(f"{status} {nome}")
        if ok:
            total_ok += 1
    
    print(f"\n📊 Resultado: {total_ok}/{len(resultados)} verificações passaram")
    
    if total_ok == len(resultados):
        print("\n🎉 SISTEMA TOTALMENTE FUNCIONAL!")
        print("   Acesse: http://localhost:8000")
        print("   Ou: http://[IP_DO_SERVIDOR]:8000")
    else:
        print("\n⚠️  Sistema com problemas.")
        print("   Verifique os itens marcados com ❌")
        
    print(f"\n📋 COMANDOS ÚTEIS:")
    print(f"   sudo supervisorctl status")
    print(f"   sudo tail -f /var/log/assessment.log")
    print(f"   sudo systemctl status postgresql")
    print(f"   curl -I http://localhost:8000")

if __name__ == "__main__":
    main()