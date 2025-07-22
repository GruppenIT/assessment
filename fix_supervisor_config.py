#!/usr/bin/env python3
"""
Script para corrigir a configuração do supervisor com escape correto
Resolve o problema de formatação na linha environment
"""

import os
import sys
from datetime import datetime

def fix_supervisor_config():
    """Corrigir configuração do supervisor com escape adequado"""
    
    supervisor_config = '/etc/supervisor/conf.d/assessment.conf'
    
    if not os.path.exists(supervisor_config):
        print(f"✗ Arquivo não encontrado: {supervisor_config}")
        return False
    
    print(f"📝 Corrigindo {supervisor_config}")
    
    try:
        # Ler configuração atual
        with open(supervisor_config, 'r') as f:
            content = f.read()
        
        print("📄 Conteúdo atual:")
        print(content)
        print("\n" + "="*50 + "\n")
        
        # Fazer backup
        backup_file = f"{supervisor_config}.backup_fix.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"💾 Backup criado: {backup_file}")
        
        # Carregar variáveis do .env
        env_vars = {}
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value.strip('\'"')
        
        # Preparar configuração correta
        new_config = f"""[program:assessment]
command={os.getcwd()}/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 main:app
directory={os.getcwd()}
user=www-data
autostart=true
autorestart=true
environment=DATABASE_URL="{env_vars.get('DATABASE_URL', '')}",SESSION_SECRET="{env_vars.get('SESSION_SECRET', '')}",FLASK_SECRET_KEY="{env_vars.get('FLASK_SECRET_KEY', '')}",FLASK_ENV="{env_vars.get('FLASK_ENV', 'production')}",TZ="{env_vars.get('TZ', 'America/Sao_Paulo')}"
stdout_logfile=/var/log/assessment.log
stderr_logfile=/var/log/assessment_error.log
redirect_stderr=true
"""
        
        print("📝 Nova configuração:")
        print(new_config)
        print("\n" + "="*50 + "\n")
        
        # Escrever nova configuração
        with open(supervisor_config, 'w') as f:
            f.write(new_config)
        
        print("✅ Configuração corrigida!")
        return True
        
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def restart_supervisor():
    """Reiniciar supervisor com nova configuração"""
    
    print("🔄 Reiniciando supervisor...")
    
    commands = [
        "sudo supervisorctl reread",
        "sudo supervisorctl update",
        "sudo supervisorctl restart assessment"
    ]
    
    for cmd in commands:
        print(f"   📡 {cmd}")
        try:
            result = os.system(cmd)
            if result == 0:
                print(f"   ✅ Sucesso")
            else:
                print(f"   ⚠️  Código de saída: {result}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 CORREÇÃO CONFIGURAÇÃO SUPERVISOR")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if fix_supervisor_config():
        print()
        restart_supervisor()
        print()
        print("=" * 60)
        print("✅ CONFIGURAÇÃO CORRIGIDA")
        print("🔄 Aguarde alguns segundos para o serviço inicializar")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ FALHA NA CORREÇÃO")
        print("=" * 60)
        sys.exit(1)