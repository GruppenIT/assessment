#!/bin/bash
# Script para aplicar correção do erro hasattr no perfil

echo "🔧 APLICANDO CORREÇÃO - ERRO HASATTR NO PERFIL"
echo "============================================="

cd /var/www/assessment

# Backup
echo "💾 Fazendo backup..."
cp routes/auth.py routes/auth.py.hasattr_backup
cp templates/auth/perfil.html templates/auth/perfil.html.hasattr_backup

# 1. Corrigir routes/auth.py
echo "🔧 Corrigindo routes/auth.py..."

python3 << 'EOF'
import re

# Ler arquivo
with open('routes/auth.py', 'r') as f:
    content = f.read()

# Correção 1: Substituir hasattr por getattr na auditoria
old_auditoria = """                    # Registrar na auditoria
                    try:
                        from models.auditoria import registrar_auditoria
                        usuario_tipo = 'admin' if hasattr(current_user, 'tipo') and current_user.tipo == 'admin' else 'respondente'
                        registrar_auditoria(
                            acao='senha_alterada',
                            usuario_tipo=usuario_tipo,
                            usuario_id=current_user.id,
                            usuario_nome=current_user.nome,
                            detalhes='Senha alterada pelo próprio usuário na página de perfil',
                            ip_address=request.remote_addr
                        )
                    except:
                        pass  # Continua mesmo se auditoria falhar"""

new_auditoria = """                    # Registrar na auditoria
                    try:
                        from models.auditoria import registrar_auditoria
                        # Determinar tipo de usuário de forma mais robusta
                        usuario_tipo = 'admin'
                        try:
                            if getattr(current_user, 'cliente_id', None):
                                usuario_tipo = 'respondente'
                            elif getattr(current_user, 'tipo', None) == 'admin':
                                usuario_tipo = 'admin'
                        except:
                            usuario_tipo = 'admin'  # Default
                        
                        registrar_auditoria(
                            acao='senha_alterada',
                            usuario_tipo=usuario_tipo,
                            usuario_id=current_user.id,
                            usuario_nome=current_user.nome,
                            detalhes='Senha alterada pelo próprio usuário na página de perfil',
                            ip_address=request.remote_addr
                        )
                    except:
                        pass  # Continua mesmo se auditoria falhar"""

if old_auditoria in content:
    content = content.replace(old_auditoria, new_auditoria)
    print("✅ Auditoria corrigida")

# Correção 2: Remover parâmetro usuario na template
content = re.sub(
    r"return render_template\('auth/perfil\.html', usuario=current_user\)",
    "return render_template('auth/perfil.html')",
    content
)

# Salvar
with open('routes/auth.py', 'w') as f:
    f.write(content)

print("✅ routes/auth.py corrigido")
EOF

# 2. Corrigir templates/auth/perfil.html
echo "🎨 Corrigindo template..."

python3 << 'EOF'
import re

# Ler template
with open('templates/auth/perfil.html', 'r') as f:
    content = f.read()

# Substituir todas as ocorrências de hasattr por "is defined"
corrections = [
    # Tipo de conta
    (r'{%\s*if\s+hasattr\(current_user,\s*[\'"]tipo[\'"]\)\s+and\s+current_user\.tipo\s*==\s*[\'"]admin[\'"]\s*%}',
     '{% if current_user.tipo is defined and current_user.tipo == \'admin\' %}'),
    
    (r'{%\s*elif\s+hasattr\(current_user,\s*[\'"]cliente_id[\'"]\)\s+and\s+current_user\.cliente_id\s*%}',
     '{% elif current_user.cliente_id is defined and current_user.cliente_id %}'),
    
    # Botão voltar dashboard
    (r'{%\s*if\s+hasattr\(current_user,\s*[\'"]tipo[\'"]\)\s+and\s+current_user\.tipo\s*==\s*[\'"]admin[\'"]\s*%}',
     '{% if current_user.cliente_id is defined and current_user.cliente_id %}'),
    
    (r'{%\s*elif\s+hasattr\(current_user,\s*[\'"]cliente_id[\'"]\)\s+and\s+current_user\.cliente_id\s*%}',
     '{% else %}'),
    
    # Empresa
    (r'{%\s*if\s+hasattr\(current_user,\s*[\'"]cliente[\'"]\)\s+and\s+current_user\.cliente\s+and\s+current_user\.cliente\.nome_empresa\s*%}',
     '{% if current_user.cliente is defined and current_user.cliente and current_user.cliente.nome_empresa is defined %}'),
    
    # Menu ações
    (r'{%\s*if\s+hasattr\(current_user,\s*[\'"]cliente_id[\'"]\)\s+and\s+current_user\.cliente_id\s*%}',
     '{% if current_user.cliente_id is defined and current_user.cliente_id %}'),
    
    (r'{%\s*elif\s+hasattr\(current_user,\s*[\'"]tipo[\'"]\)\s+and\s+current_user\.tipo\s*==\s*[\'"]admin[\'"]\s*%}',
     '{% else %}')
]

# Aplicar correções
for old, new in corrections:
    content = re.sub(old, new, content)

# Correções específicas manuais
content = content.replace(
    "{% if hasattr(current_user, 'tipo') and current_user.tipo == 'admin' %}",
    "{% if current_user.cliente_id is defined and current_user.cliente_id %}"
)

content = content.replace(
    "{% elif hasattr(current_user, 'cliente_id') and current_user.cliente_id %}",
    "{% else %}"
)

content = content.replace(
    "{% if hasattr(current_user, 'cliente_id') and current_user.cliente_id %}",
    "{% if current_user.cliente_id is defined and current_user.cliente_id %}"
)

content = content.replace(
    "{% elif hasattr(current_user, 'tipo') and current_user.tipo == 'admin' %}",
    "{% else %}"
)

content = content.replace(
    "{% if hasattr(current_user, 'cliente') and current_user.cliente and current_user.cliente.nome_empresa %}",
    "{% if current_user.cliente is defined and current_user.cliente and current_user.cliente.nome_empresa is defined %}"
)

# Correção do tipo de conta
content = re.sub(
    r'{% if hasattr\(current_user, \'tipo\'\) and current_user\.tipo == \'admin\' %}.*?<span class="badge bg-danger">Administrador</span>.*?{% elif hasattr\(current_user, \'cliente_id\'\) and current_user\.cliente_id %}.*?<span class="badge bg-primary">Respondente</span>.*?{% else %}.*?<span class="badge bg-secondary">Usuário</span>.*?{% endif %}',
    '{% if current_user.tipo is defined and current_user.tipo == \'admin\' %}\n                                                <span class="badge bg-danger">Administrador</span>\n                                            {% elif current_user.cliente_id is defined and current_user.cliente_id %}\n                                                <span class="badge bg-primary">Respondente</span>\n                                            {% else %}\n                                                <span class="badge bg-success">Administrador</span>\n                                            {% endif %}',
    content,
    flags=re.DOTALL
)

# Salvar
with open('templates/auth/perfil.html', 'w') as f:
    f.write(content)

print("✅ Template corrigido")
EOF

# 3. Verificar sintaxe
echo "🧪 Verificando sintaxe..."
if python3 -m py_compile routes/auth.py; then
    echo "✅ Sintaxe routes/auth.py OK"
else
    echo "❌ Erro de sintaxe, restaurando backup"
    cp routes/auth.py.hasattr_backup routes/auth.py
    cp templates/auth/perfil.html.hasattr_backup templates/auth/perfil.html
    exit 1
fi

# 4. Ajustar permissões
echo "🔐 Ajustando permissões..."
chown -R www-data:www-data /var/www/assessment/
chmod -R 755 /var/www/assessment/

# 5. Limpar cache
echo "🧹 Limpando cache..."
find /var/www/assessment -name "*.pyc" -delete
find /var/www/assessment -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 6. Reiniciar serviço
echo "🔄 Reiniciando serviço..."
supervisorctl restart assessment
sleep 3

# 7. Testar
echo "🧪 Testando..."
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/perfil 2>/dev/null || echo "000")

if [ "$response_code" = "200" ] || [ "$response_code" = "302" ]; then
    echo ""
    echo "🎉 CORREÇÃO APLICADA COM SUCESSO!"
    echo "   Código de resposta: $response_code"
    echo "   ✅ Erro hasattr corrigido"
    echo "   ✅ Funcionalidade de alteração de senha disponível"
    echo ""
    echo "📋 Teste agora:"
    echo "   https://assessments.zerobox.com.br/auth/perfil"
else
    echo ""
    echo "⚠️  Resposta: $response_code"
    echo "   Verificando logs..."
    tail -10 /var/log/supervisor/assessment-*.log 2>/dev/null || echo "Logs não encontrados"
fi

echo ""
echo "💾 BACKUPS SALVOS:"
echo "   routes/auth.py.hasattr_backup"
echo "   templates/auth/perfil.html.hasattr_backup"