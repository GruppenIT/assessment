"""
Carregador de variáveis de ambiente do arquivo .env
Este módulo é importado no início da aplicação para garantir
que as variáveis do .env sejam sempre carregadas
"""

import os

def load_env():
    """Carregar variáveis do arquivo .env"""
    env_files = ['.env', '/home/suporte/.env']
    
    for env_file in env_files:
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remover aspas se existirem
                            value = value.strip('\'"')
                            # Aplicar no environment
                            os.environ[key] = value
                print(f"ENV_LOADER: Carregadas variáveis de {env_file}")
                return True
            except Exception as e:
                print(f"ENV_LOADER: Erro ao carregar {env_file}: {e}")
                continue
    
    print("ENV_LOADER: Nenhum arquivo .env encontrado")
    return False

# Carregar automaticamente quando este módulo for importado
load_env()