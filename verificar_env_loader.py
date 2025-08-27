#!/usr/bin/env python3
"""
Script para verificar se o env_loader.py está funcionando corretamente
"""

import os
import sys

def verificar_env_loader():
    """Verifica se o env_loader carrega as variáveis corretamente"""
    
    print("🔍 VERIFICAÇÃO DO ENV_LOADER")
    print("="*40)
    
    # Testar carregamento do env_loader
    try:
        # Limpar variáveis existentes para teste
        env_vars = ['DATABASE_URL', 'SESSION_SECRET', 'FLASK_SECRET_KEY']
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Importar env_loader
        sys.path.insert(0, '/var/www/assessment')
        import env_loader
        
        print("✅ env_loader.py importado com sucesso")
        
        # Verificar se as variáveis foram carregadas
        required_vars = {
            'DATABASE_URL': 'postgresql://assessment_user:P@ssw0rd@.!@localhost/assessment_db',
            'SESSION_SECRET': '9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=',
            'FLASK_SECRET_KEY': '9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=',
            'FLASK_ENV': 'production',
            'TZ': 'America/Sao_Paulo'
        }
        
        print("\n📋 Verificando variáveis de ambiente:")
        all_loaded = True
        
        for var, expected in required_vars.items():
            actual = os.environ.get(var)
            if actual:
                # Mascarar dados sensíveis na exibição
                if 'SECRET' in var or 'PASSWORD' in var:
                    display_value = actual[:10] + "..." if len(actual) > 10 else "***"
                    expected_display = expected[:10] + "..." if len(expected) > 10 else "***"
                else:
                    display_value = actual
                    expected_display = expected
                
                status = "✅" if actual == expected else "❌"
                print(f"  {status} {var}: {display_value}")
                
                if actual != expected:
                    print(f"    Esperado: {expected_display}")
                    all_loaded = False
            else:
                print(f"  ❌ {var}: NÃO ENCONTRADA")
                all_loaded = False
        
        if all_loaded:
            print("\n🎉 TODAS AS VARIÁVEIS CARREGADAS CORRETAMENTE!")
        else:
            print("\n⚠️ ALGUMAS VARIÁVEIS NÃO FORAM CARREGADAS")
            
    except Exception as e:
        print(f"❌ Erro ao verificar env_loader: {e}")
        return False
    
    return all_loaded

if __name__ == "__main__":
    # Verificar se estamos executando como root ou com sudo
    if os.geteuid() == 0:
        print("⚠️ Executando como root - mudando para o diretório correto")
        os.chdir('/var/www/assessment')
    
    verificar_env_loader()