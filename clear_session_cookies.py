#!/usr/bin/env python3
"""
Script para limpar todas as sessões e cookies ativos
"""

import os
import glob

def clear_all_sessions():
    """Remove todos os arquivos de cookies e sessões ativas"""
    
    print("🧹 LIMPANDO SESSÕES E COOKIES")
    print("="*40)
    
    # Arquivos de cookies que podem existir
    cookie_files = [
        'cookies.txt',
        'cookies_*.txt',
        'flask_session_*',
        '.cookies'
    ]
    
    removed_count = 0
    
    # Remover arquivos de cookies
    for pattern in cookie_files:
        files = glob.glob(pattern)
        for file in files:
            try:
                os.remove(file)
                print(f"✅ Removido: {file}")
                removed_count += 1
            except Exception as e:
                print(f"⚠️  Erro ao remover {file}: {e}")
    
    # Limpar variáveis de ambiente de sessão se existirem
    env_vars = ['FLASK_SESSION', 'SESSION_ID', 'AUTH_TOKEN']
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"✅ Variável {var} removida")
            removed_count += 1
    
    print(f"\n📊 RESUMO:")
    print(f"   {removed_count} itens removidos")
    print(f"\n💡 PARA TESTAR COMPLETAMENTE:")
    print("   1. Feche todos os navegadores")
    print("   2. Abra nova aba anônima/incógnita") 
    print("   3. Acesse: http://localhost:5000/admin/projetos/working")
    print("   4. Deve ser redirecionado para login")

if __name__ == "__main__":
    clear_all_sessions()