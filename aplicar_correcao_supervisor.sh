#!/bin/bash
# Script para aplicar correção do Supervisor no ambiente on-premise

echo "🔧 APLICANDO CORREÇÃO DO SUPERVISOR"
echo "=================================="

# 1. Criar arquivo .env com as variáveis corretas
echo "📝 Criando arquivo .env..."
sudo tee /var/www/assessment/.env << 'EOF'
DATABASE_URL=postgresql://assessment_user:P@ssw0rd@.!@localhost/assessment_db
SESSION_SECRET=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_SECRET_KEY=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_ENV=production
TZ=America/Sao_Paulo
EOF

# 2. Configurar permissões do arquivo .env
echo "🔒 Configurando permissões..."
sudo chown www-data:www-data /var/www/assessment/.env
sudo chmod 600 /var/www/assessment/.env

# 3. Criar nova configuração do Supervisor (sem environment inline)
echo "⚙️ Atualizando configuração do Supervisor..."
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

# 4. Parar serviços antes de recarregar
echo "🛑 Parando serviços..."
sudo supervisorctl stop assessment 2>/dev/null || true

# 5. Recarregar configuração do Supervisor
echo "🔄 Recarregando Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update

# 6. Iniciar o serviço
echo "🚀 Iniciando serviço assessment..."
sudo supervisorctl start assessment

# 7. Verificar status
echo "📊 Status do serviço:"
sudo supervisorctl status assessment

echo ""
echo "✅ CORREÇÃO APLICADA!"
echo ""
echo "🔍 Para verificar se funcionou:"
echo "  sudo supervisorctl status"
echo "  sudo tail -f /var/log/assessment.log"
echo ""
echo "🔧 Se ainda houver problemas:"
echo "  sudo tail -f /var/log/assessment_error.log"
echo "  sudo journalctl -u supervisor -f"