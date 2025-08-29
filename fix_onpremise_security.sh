#!/bin/bash
# Script específico para corrigir segurança no servidor on-premise porta 8000

echo "🔐 CORRIGINDO SEGURANÇA NO SERVIDOR ON-PREMISE"
echo "=============================================="

cd /var/www/assessment

# 1. Backup completo
echo "📋 Criando backup completo..."
backup_dir="/var/www/assessment/backup_security_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$backup_dir"
sudo cp -r app.py routes/ templates/ utils/ "$backup_dir/"
echo "   ✅ Backup criado: $backup_dir"

# 2. Parar serviços
echo "🛑 Parando serviços..."
sudo supervisorctl stop assessment

# 3. Aplicar patch no app.py - adicionar middleware de segurança
echo "🔒 Aplicando middleware de segurança no app.py..."

# Backup do app.py atual
sudo cp app.py app.py.bak

# Criar versão corrigida do app.py com middleware
sudo bash -c 'cat > /tmp/security_patch.py << '"'"'EOF'"'"'
# Patch para adicionar middleware de segurança após a criação da app

# Adicionar após a linha que contém "app.register_blueprint"
MIDDLEWARE_CODE = """
    
    # Middleware global de proteção de autenticação
    @app.before_request
    def require_login():
        from flask import request, redirect, url_for, flash
        from flask_login import current_user
        
        # Rotas públicas que não requerem autenticação
        rotas_publicas = [
            "auth.login",
            "auth.logout", 
            "static",
            "home_redirect"
        ]
        
        # Caminhos que sempre devem ser permitidos
        caminhos_publicos = [
            "/static/",
            "/favicon.ico"
        ]
        
        # Verificar se é caminho público
        for caminho in caminhos_publicos:
            if request.path.startswith(caminho):
                return
        
        # Verificar se é rota pública
        endpoint = request.endpoint
        if endpoint and any(endpoint.startswith(rota) for rota in rotas_publicas):
            return
        
        # Se não está autenticado e não é rota pública, redirecionar para login
        if not current_user.is_authenticated:
            flash("Acesso restrito. Por favor, faça login.", "warning")
            return redirect(url_for("auth.login", next=request.url))
"""

import re

# Ler arquivo atual
with open("/var/www/assessment/app.py", "r") as f:
    content = f.read()

# Procurar local para inserir o middleware (após os blueprints)
if "@app.before_request" not in content:
    # Inserir após a última linha de register_blueprint
    pattern = r"(app\.register_blueprint\([^)]+\)[^\n]*\n)"
    matches = list(re.finditer(pattern, content))
    if matches:
        last_match = matches[-1]
        insert_pos = last_match.end()
        new_content = content[:insert_pos] + MIDDLEWARE_CODE + content[insert_pos:]
        
        with open("/var/www/assessment/app.py", "w") as f:
            f.write(new_content)
        print("✅ Middleware de segurança adicionado ao app.py")
    else:
        print("❌ Não foi possível encontrar local para inserir middleware")
else:
    print("ℹ️  Middleware já existe no app.py")
EOF

python3 /tmp/security_patch.py'

# 4. Remover rotas de auto-login de routes/auth.py
echo "🗑️  Removendo rotas de auto-login..."
sudo sed -i '/^@auth_bp\.route.*auto.*login/,/^@auth_bp\.route\|^def [a-zA-Z]/{ /^@auth_bp\.route\|^def [a-zA-Z]/!d; }' routes/auth.py
sudo sed -i '/^def auto_login/,/^@\|^def /{ /^def auto_login/d; /^@\|^def [^a]/!d; }' routes/auth.py

# 5. Proteger routes/cliente_portal.py
echo "🛡️  Protegendo cliente_portal.py..."
if ! grep -q "@login_required" routes/cliente_portal.py; then
    sudo sed -i '1i from flask_login import login_required' routes/cliente_portal.py
    sudo sed -i '/^@cliente_portal_bp\.route/a @login_required' routes/cliente_portal.py
fi

# 6. Verificar e corrigir sintaxe em routes/projeto.py
echo "🔧 Verificando routes/projeto.py..."
sudo sed -i '/^@sistema\.com/,/return "Admin não encontrado"$/d' routes/projeto.py

# 7. Testar sintaxe Python
echo "🧪 Testando sintaxe Python..."
if sudo python3 -m py_compile app.py; then
    echo "   ✅ app.py - sintaxe OK"
else
    echo "   ❌ app.py - erro de sintaxe, restaurando backup"
    sudo cp app.py.bak app.py
fi

# 8. Reiniciar serviços
echo "🔄 Reiniciando serviços..."
sudo supervisorctl start assessment
sleep 5

# 9. Verificar se está rodando
echo "📊 Verificando status..."
sudo supervisorctl status assessment

# 10. Testar segurança
echo "🔍 Testando segurança..."
echo "   Testando rota protegida na porta 8000:"

response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/projetos/working)
if [ "$response_code" = "302" ]; then
    echo "   ✅ SUCESSO! Rota protegida (código $response_code - redirecionando para login)"
elif [ "$response_code" = "200" ]; then
    echo "   ❌ FALHA! Rota ainda acessível sem login (código $response_code)"
    echo "   🔍 Verificando logs de erro..."
    sudo tail -n 20 /var/log/supervisor/supervisord.log | grep -i error
else
    echo "   ⚠️  Resposta inesperada: código $response_code"
fi

# 11. Verificar logs por erros
echo "   Verificando logs por erros recentes..."
if sudo tail -n 10 /var/log/assessment.log | grep -i error > /dev/null 2>&1; then
    echo "   ⚠️  Erros encontrados nos logs:"
    sudo tail -n 10 /var/log/assessment.log | grep -i error
else
    echo "   ✅ Nenhum erro crítico nos logs"
fi

echo ""
echo "🎯 RESULTADO FINAL:"
echo "=================="

final_test=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/dashboard)
if [ "$final_test" = "302" ]; then
    echo "✅ SEGURANÇA APLICADA COM SUCESSO!"
    echo "   • Todas as rotas agora requerem login"
    echo "   • Usuários são redirecionados para /auth/login"
    echo "   • Sistema protegido contra acesso não autorizado"
else
    echo "❌ SEGURANÇA NÃO APLICADA CORRETAMENTE"
    echo "   • Código de resposta: $final_test"
    echo "   • É necessário investigação manual"
    echo "   • Backup disponível em: $backup_dir"
fi

echo ""
echo "📋 PARA MONITORAR:"
echo "   sudo tail -f /var/log/assessment.log"
echo "   sudo supervisorctl status assessment"
echo ""
echo "🔄 PARA REVERTER (se necessário):"
echo "   sudo cp $backup_dir/app.py /var/www/assessment/"
echo "   sudo supervisorctl restart assessment"