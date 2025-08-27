#!/usr/bin/env python3
"""
Script para corrigir configuração do Supervisor com variáveis de ambiente problemáticas
Resolve o erro de "Format string badly formatted" causado por caracteres especiais
"""

import os
import sys
import subprocess

def fix_supervisor_config():
    """Corrige a configuração do Supervisor para usar arquivo .env"""
    
    print("🔧 CORREÇÃO DA CONFIGURAÇÃO DO SUPERVISOR")
    print("="*60)
    
    # Configuração corrigida do Supervisor
    supervisor_config = """[program:assessment]
command=/var/www/assessment/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 main:app
directory=/var/www/assessment
user=www-data
autostart=true
autorestart=true
environment=PATH="/var/www/assessment/venv/bin"
stdout_logfile=/var/log/assessment.log
stderr_logfile=/var/log/assessment_error.log
redirect_stderr=true
"""
    
    # Arquivo .env para as variáveis de ambiente
    env_content = """# Configurações do Sistema de Assessment
DATABASE_URL=postgresql://assessment_user:P@ssw0rd@.!@localhost/assessment_db
SESSION_SECRET=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_SECRET_KEY=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_ENV=production
TZ=America/Sao_Paulo
"""
    
    print("📝 NOVA CONFIGURAÇÃO DO SUPERVISOR:")
    print(supervisor_config)
    
    print("\n📝 ARQUIVO .env A SER CRIADO:")
    print(env_content)
    
    print("\n🔍 PROBLEMA IDENTIFICADO:")
    print("- Caracteres % na URL do banco estavam sendo interpretados como placeholders")
    print("- Supervisor não consegue processar strings com formatação complexa")
    print("- Solução: usar arquivo .env para variáveis de ambiente")
    
    print("\n✅ COMANDOS PARA APLICAR A CORREÇÃO:")
    print("""
# 1. Criar arquivo .env
sudo tee /var/www/assessment/.env << 'EOF'
DATABASE_URL=postgresql://assessment_user:P@ssw0rd@.!@localhost/assessment_db
SESSION_SECRET=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_SECRET_KEY=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_ENV=production
TZ=America/Sao_Paulo
EOF

# 2. Corrigir permissões
sudo chown www-data:www-data /var/www/assessment/.env
sudo chmod 600 /var/www/assessment/.env

# 3. Atualizar configuração do Supervisor
sudo tee /etc/supervisor/conf.d/assessment.conf << 'EOF'
[program:assessment]
command=/var/www/assessment/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 main:app
directory=/var/www/assessment
user=www-data
autostart=true
autorestart=true
environment=PATH="/var/www/assessment/venv/bin"
stdout_logfile=/var/log/assessment.log
stderr_logfile=/var/log/assessment_error.log
redirect_stderr=true
EOF

# 4. Recarregar Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start assessment

# 5. Verificar status
sudo supervisorctl status assessment
""")
    
    print("\n📋 VERIFICAÇÕES ADICIONAIS:")
    print("- Confirme que env_loader.py está carregando o arquivo .env")
    print("- Verifique se o banco PostgreSQL está acessível")
    print("- Teste a aplicação manualmente antes de usar o Supervisor")
    
    print("\n🎯 RESULTADO ESPERADO:")
    print("- Supervisor iniciará sem erros de formatação")
    print("- Aplicação carregará variáveis do arquivo .env")
    print("- Sistema funcionará normalmente em produção")

if __name__ == "__main__":
    fix_supervisor_config()