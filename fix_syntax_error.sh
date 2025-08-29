#!/bin/bash
# Script para corrigir erro de sintaxe no servidor on-premise

echo "🔧 CORRIGINDO ERRO DE SINTAXE"
echo "=========================="

cd /var/www/assessment

# 1. Restaurar backup original
echo "📋 Restaurando backup original..."
if [ -f "app.py.backup_1756498913" ]; then
    sudo cp app.py.backup_1756498913 app.py
    echo "   ✅ Backup restaurado"
else
    echo "   ❌ Backup não encontrado"
    exit 1
fi

# 2. Aplicar patch mais seguro - adicionar middleware no final do arquivo
echo "🔒 Aplicando middleware seguro..."

# Criar arquivo temporário com o middleware correto
cat > /tmp/middleware_patch.py << 'EOF'
# Middleware de segurança - adicionar no final do create_app()

middleware_code = '''
    # Middleware global de proteção de autenticação
    @app.before_request
    def require_login():
        from flask import request, redirect, url_for, flash
        from flask_login import current_user
        
        # Rotas públicas que não requerem autenticação
        rotas_publicas = [
            'auth.login',
            'auth.logout',
            'static'
        ]
        
        # Caminhos que sempre devem ser permitidos
        caminhos_publicos = [
            '/static/',
            '/favicon.ico'
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
            flash('Acesso restrito. Por favor, faça login.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
'''

# Ler arquivo app.py
with open('/var/www/assessment/app.py', 'r') as f:
    content = f.read()

# Procurar pelo final da função create_app (antes do return app)
import re

# Encontrar a linha "return app" no final da função create_app
pattern = r'(\s+return app\s*\n)'
match = re.search(pattern, content)

if match:
    # Inserir middleware antes do return app
    insert_pos = match.start()
    new_content = content[:insert_pos] + middleware_code + content[insert_pos:]
    
    # Escrever arquivo modificado
    with open('/var/www/assessment/app.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Middleware adicionado com sucesso")
else:
    print("❌ Não foi possível encontrar 'return app' para inserir middleware")
    exit(1)
EOF

# Executar o patch Python
python3 /tmp/middleware_patch.py

# 3. Verificar sintaxe
echo "🧪 Verificando sintaxe..."
if python3 -c "import sys; sys.path.append('/var/www/assessment'); import app" 2>/dev/null; then
    echo "   ✅ Sintaxe OK"
else
    echo "   ❌ Erro de sintaxe detectado, mostrando detalhes:"
    python3 -c "import sys; sys.path.append('/var/www/assessment'); import app" 2>&1 | head -10
    echo "   🔄 Restaurando backup novamente..."
    sudo cp app.py.backup_1756498913 app.py
    exit 1
fi

# 4. Tentar reiniciar serviço
echo "🔄 Tentando reiniciar serviço..."
sudo supervisorctl start assessment
sleep 3

# 5. Verificar status
echo "📊 Verificando status..."
status=$(sudo supervisorctl status assessment)
echo "   $status"

if echo "$status" | grep -q "RUNNING"; then
    echo "   ✅ Serviço rodando"
    
    # Testar segurança
    echo "🔍 Testando segurança..."
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/projetos/working)
    if [ "$response" = "302" ]; then
        echo "   ✅ SUCESSO! Segurança ativada (código $response)"
    else
        echo "   ⚠️  Código de resposta: $response (esperado: 302)"
    fi
else
    echo "   ❌ Serviço não está rodando"
    echo "   📋 Logs recentes:"
    sudo tail -5 /var/log/assessment.log 2>/dev/null || echo "      (logs não disponíveis)"
fi

echo ""
echo "📋 Status final:"
sudo supervisorctl status assessment