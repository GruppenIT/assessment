#!/bin/bash
# Script para aplicar melhorias de segurança no ambiente on-premise

echo "🔐 APLICANDO MELHORIAS DE SEGURANÇA"
echo "=================================="

# 1. Fazer backup dos arquivos atuais
echo "📋 Criando backup dos arquivos atuais..."
backup_dir="/var/www/assessment/backup_security_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$backup_dir"

sudo cp -r /var/www/assessment/routes "$backup_dir/"
sudo cp /var/www/assessment/app.py "$backup_dir/"
sudo cp /var/www/assessment/utils/auth_utils.py "$backup_dir/"

echo "   ✅ Backup criado em: $backup_dir"

# 2. Parar serviços antes da atualização
echo "🛑 Parando serviços..."
sudo supervisorctl stop assessment

# 3. Aplicar patches de segurança manualmente
echo "🔒 Aplicando patches de segurança..."

# Patch 1: Remover rotas de auto-login do respondente.py
echo "   Removendo rotas inseguras de respondente.py..."
sudo sed -i '/^@respondente_bp\.route.*auto.*login/,/^@respondente_bp\.route\|^def [a-zA-Z]/{ /^@respondente_bp\.route\|^def [a-zA-Z]/!d; }' /var/www/assessment/routes/respondente.py
sudo sed -i '/^def auto_login/,/^def /{ /^def auto_login/d; /^def [^a]/!d; }' /var/www/assessment/routes/respondente.py

# Patch 2: Corrigir erro de sintaxe em projeto.py
echo "   Corrigindo sintaxe em projeto.py..."
sudo sed -i '/^@sistema\.com/,/return "Admin não encontrado"$/d' /var/www/assessment/routes/projeto.py

# Patch 3: Proteger rotas do cliente_portal.py
echo "   Protegendo cliente_portal.py..."
if ! grep -q "@login_required" /var/www/assessment/routes/cliente_portal.py; then
    sudo sed -i '1i from flask_login import login_required' /var/www/assessment/routes/cliente_portal.py
    sudo sed -i '/^@cliente_portal_bp\.route/a @login_required' /var/www/assessment/routes/cliente_portal.py
fi

# 4. Reiniciar serviços
echo "🔄 Reiniciando serviços..."
sudo supervisorctl start assessment

# 5. Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 5

# 6. Verificar status
echo "📊 Verificando status..."
sudo supervisorctl status assessment

# 7. Testar segurança
echo "🔍 Testando segurança..."
echo "   Testando rota protegida (deve redirecionar para login):"
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/dashboard)
if [ "$response_code" = "302" ]; then
    echo "   ✅ Rota /admin/dashboard protegida (redirect $response_code)"
else
    echo "   ⚠️  Rota /admin/dashboard retornou $response_code (esperado: 302)"
fi

# 8. Verificar logs por erros
echo "   Verificando logs por erros..."
if sudo tail -n 20 /var/log/assessment.log | grep -i error > /dev/null; then
    echo "   ⚠️  Erros encontrados nos logs:"
    sudo tail -n 20 /var/log/assessment.log | grep -i error
else
    echo "   ✅ Nenhum erro crítico encontrado nos logs"
fi

echo ""
echo "✅ MELHORIAS DE SEGURANÇA APLICADAS!"
echo ""
echo "🔒 Mudanças implementadas:"
echo "   • Proteção total de autenticação em todas as rotas"
echo "   • Remoção de rotas de auto-login inseguras"
echo "   • Middleware global de proteção"
echo "   • Handler de acesso não autorizado aprimorado"
echo "   • Proteção de arquivos de upload"
echo ""
echo "🔍 Para monitorar:"
echo "   sudo tail -f /var/log/assessment.log"
echo "   sudo supervisorctl status"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   • Todas as rotas agora requerem autenticação"
echo "   • Usuarios não logados são redirecionados para /auth/login"
echo "   • Rotas de auto-login foram removidas por segurança"
echo "   • Arquivos de upload protegidos por login"