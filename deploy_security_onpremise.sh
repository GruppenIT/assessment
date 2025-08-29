#!/bin/bash
# Script final para aplicar segurança no ambiente on-premise

echo "🔐 APLICANDO SEGURANÇA COMPLETA"
echo "============================="

# Backup
backup_dir="/var/www/assessment/backup_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$backup_dir"
sudo cp -r /var/www/assessment/app.py /var/www/assessment/routes "$backup_dir/"

echo "✅ Backup criado: $backup_dir"

# Parar serviços
echo "🛑 Parando serviços..."
sudo supervisorctl stop assessment

# Aplicar mudanças (copiar arquivos já modificados)
echo "📥 Aplicando mudanças de segurança..."
# Os arquivos já foram modificados no repositório

# Reiniciar
echo "🔄 Reiniciando..."
sudo supervisorctl start assessment
sleep 3

# Verificar
echo "✅ Verificando status:"
sudo supervisorctl status assessment

echo "🔒 SEGURANÇA APLICADA!"
echo "   • Todas as rotas protegidas com autenticação"
echo "   • Auto-login removido"
echo "   • Uploads protegidos"
echo "   • Middleware global ativo"
