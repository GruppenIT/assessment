#!/usr/bin/env python3
"""
Script para carregar variáveis do .env e aplicar na configuração do supervisor
Corrige o problema onde .env existe mas não é carregado pela aplicação
"""

import os
import sys
from datetime import datetime

def load_env_file():
    """Carregar variáveis do arquivo .env"""
    env_vars = {}
    
    env_paths = ['.env', '/home/suporte/.env']
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"📄 Carregando {env_path}")
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key] = value.strip('\'"')
                break
            except Exception as e:
                print(f"✗ Erro ao ler {env_path}: {e}")
                continue
    
    return env_vars

def update_supervisor_config(env_vars):
    """Atualizar configuração do supervisor com variáveis de ambiente"""
    
    supervisor_config = '/etc/supervisor/conf.d/assessment.conf'
    
    if not os.path.exists(supervisor_config):
        print(f"✗ Arquivo de configuração não encontrado: {supervisor_config}")
        return False
    
    print(f"📝 Atualizando {supervisor_config}")
    
    try:
        # Ler configuração atual
        with open(supervisor_config, 'r') as f:
            content = f.read()
        
        # Preparar linha de environment
        env_line = "environment="
        env_pairs = []
        
        important_vars = ['DATABASE_URL', 'SESSION_SECRET', 'FLASK_SECRET_KEY', 'FLASK_ENV']
        
        for var in important_vars:
            if var in env_vars:
                env_pairs.append(f'{var}="{env_vars[var]}"')
        
        if env_pairs:
            env_line += ",".join(env_pairs)
            
            # Verificar se já existe linha environment
            lines = content.split('\n')
            updated_lines = []
            env_added = False
            
            for line in lines:
                if line.strip().startswith('environment='):
                    updated_lines.append(env_line)
                    env_added = True
                    print(f"   ✓ Atualizou linha environment existente")
                else:
                    updated_lines.append(line)
            
            if not env_added:
                # Adicionar environment após command
                for i, line in enumerate(updated_lines):
                    if line.strip().startswith('command='):
                        updated_lines.insert(i + 1, env_line)
                        print(f"   ✓ Adicionou nova linha environment")
                        break
            
            # Escrever configuração atualizada
            new_content = '\n'.join(updated_lines)
            
            # Fazer backup
            backup_file = f"{supervisor_config}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_file, 'w') as f:
                f.write(content)
            print(f"   💾 Backup criado: {backup_file}")
            
            # Escrever nova configuração
            with open(supervisor_config, 'w') as f:
                f.write(new_content)
            
            print("   ✓ Configuração do supervisor atualizada")
            return True
        else:
            print("   ⚠️  Nenhuma variável importante encontrada no .env")
            return False
            
    except Exception as e:
        print(f"   ✗ Erro ao atualizar supervisor: {e}")
        return False

def create_systemd_env_file(env_vars):
    """Criar arquivo de ambiente para systemd (alternativa)"""
    
    env_file = '/etc/systemd/system/assessment.env'
    
    try:
        print(f"📝 Criando {env_file}")
        
        with open(env_file, 'w') as f:
            f.write("# Variáveis de ambiente para o sistema de assessment\n")
            f.write(f"# Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for key, value in env_vars.items():
                f.write(f'{key}="{value}"\n')
        
        print(f"   ✓ Arquivo criado: {env_file}")
        return True
        
    except Exception as e:
        print(f"   ✗ Erro ao criar arquivo systemd: {e}")
        return False

def restart_services():
    """Reiniciar serviços necessários"""
    
    print("🔄 Reiniciando serviços...")
    
    commands = [
        "sudo supervisorctl reread",
        "sudo supervisorctl update", 
        "sudo supervisorctl restart assessment"
    ]
    
    for cmd in commands:
        try:
            print(f"   📡 {cmd}")
            result = os.system(cmd)
            if result == 0:
                print(f"   ✓ Sucesso")
            else:
                print(f"   ⚠️  Código de saída: {result}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 CORREÇÃO DE CARREGAMENTO DO .ENV")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Carregar variáveis do .env
    env_vars = load_env_file()
    
    if not env_vars:
        print("❌ Nenhuma variável encontrada no .env")
        sys.exit(1)
    
    print(f"✓ Carregadas {len(env_vars)} variáveis do .env")
    
    # Mostrar variáveis carregadas (mascarando senhas)
    print("\n📋 Variáveis carregadas:")
    for key, value in env_vars.items():
        if 'PASSWORD' in key or 'SECRET' in key:
            print(f"   🔑 {key}=***")
        elif 'DATABASE_URL' in key and '@' in value:
            parts = value.split('@')
            masked = parts[0].split(':')[0] + ':***@' + '@'.join(parts[1:])
            print(f"   🔗 {key}={masked}")
        else:
            print(f"   🔧 {key}={value}")
    
    print()
    
    # Atualizar configuração do supervisor
    if update_supervisor_config(env_vars):
        print("✅ Configuração do supervisor atualizada")
    else:
        print("⚠️  Não foi possível atualizar supervisor")
    
    print()
    
    # Criar arquivo systemd como alternativa
    create_systemd_env_file(env_vars)
    
    print()
    
    # Reiniciar serviços
    restart_services()
    
    print()
    print("=" * 60)
    print("✅ CORREÇÃO CONCLUÍDA")
    print("📝 As variáveis do .env agora devem estar disponíveis")
    print("🔄 Aguarde alguns segundos e teste novamente o sistema")
    print("=" * 60)