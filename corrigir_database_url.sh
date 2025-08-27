#!/bin/bash
# Script para corrigir a URL do banco de dados no arquivo .env

echo "🔧 CORRIGINDO URL DO BANCO DE DADOS"
echo "=================================="

# O erro mostra: "could not translate host name "ssw0rd@.!@localhost""
# Isso indica que a URL está sendo mal interpretada
# A URL correta deve ter escape dos caracteres especiais

echo "📝 Atualizando arquivo .env com URL corrigida..."

# Criar nova versão do arquivo .env com URL corrigida
sudo tee /var/www/assessment/.env << 'EOF'
DATABASE_URL=postgresql://assessment_user:P%40ssw0rd%40.%21@localhost/assessment_db
SESSION_SECRET=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_SECRET_KEY=9JUijS0Z9csNkHM2ssAXXirRPsW0MSA3Ax1yACVWqxs=
FLASK_ENV=production
TZ=America/Sao_Paulo
EOF

echo "🔒 Configurando permissões..."
sudo chown www-data:www-data /var/www/assessment/.env
sudo chmod 600 /var/www/assessment/.env

echo "📋 Comparação das URLs:"
echo "❌ Anterior: postgresql://assessment_user:P@ssw0rd@.!@localhost/assessment_db"
echo "✅ Corrigida: postgresql://assessment_user:P%40ssw0rd%40.%21@localhost/assessment_db"
echo ""
echo "📖 Explicação dos escapes:"
echo "  @ vira %40 (código ASCII para @)"
echo "  ! vira %21 (código ASCII para !)"
echo ""

echo "🔄 Reiniciando serviço assessment..."
sudo supervisorctl restart assessment

echo "⏳ Aguardando inicialização..."
sleep 3

echo "📊 Status do serviço:"
sudo supervisorctl status assessment

echo ""
echo "✅ CORREÇÃO APLICADA!"
echo ""
echo "🔍 Para verificar se funcionou:"
echo "  sudo tail -f /var/log/assessment.log"
echo "  sudo supervisorctl status"
echo ""
echo "🌐 Se tudo estiver OK, teste acessando:"
echo "  http://localhost:8000"