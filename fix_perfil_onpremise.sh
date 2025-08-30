#!/bin/bash
# Script simplificado para corrigir erro do perfil on-premise

echo "🔧 CORREÇÃO EMERGENCIAL - PERFIL ON-PREMISE"
echo "=========================================="

cd /var/www/assessment

# 1. Backup dos arquivos
echo "📋 Criando backup..."
cp routes/auth.py routes/auth.py.emergency_backup
cp templates/auth/perfil.html templates/auth/perfil.html.emergency_backup
echo "   ✅ Backup criado"

# 2. Corrigir routes/auth.py
echo "🔧 Corrigindo routes/auth.py..."

# Remover import AlterarSenhaForm se existir
sed -i 's/from forms\.auth_forms import LoginForm, AlterarSenhaForm/from forms.auth_forms import LoginForm/g' routes/auth.py

# Criar nova função perfil
cat > /tmp/new_perfil.py << 'EOF'
@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Página de perfil do usuário com opção de alterar senha"""
    
    # Processar alteração de senha
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '').strip()
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar_nova_senha = request.form.get('confirmar_nova_senha', '').strip()
        
        # Validações
        if not senha_atual:
            flash('Senha atual é obrigatória.', 'danger')
        elif not nova_senha:
            flash('Nova senha é obrigatória.', 'danger')
        elif len(nova_senha) < 6:
            flash('Nova senha deve ter pelo menos 6 caracteres.', 'danger')
        elif nova_senha != confirmar_nova_senha:
            flash('Confirmação de senha não confere.', 'danger')
        elif not check_password_hash(current_user.senha_hash, senha_atual):
            flash('Senha atual incorreta.', 'danger')
        else:
            # Alterar senha
            try:
                current_user.senha_hash = generate_password_hash(nova_senha)
                db.session.commit()
                flash('Senha alterada com sucesso!', 'success')
                return redirect(url_for('auth.perfil'))
            except Exception as e:
                db.session.rollback()
                flash('Erro ao alterar senha. Tente novamente.', 'danger')
    
    return render_template('auth/perfil.html', usuario=current_user)
EOF

# Remover função perfil antiga e adicionar nova
python3 << 'EOF'
import re

with open('routes/auth.py', 'r') as f:
    content = f.read()

# Remover função perfil existente
pattern = r'@auth_bp\.route\(\'/perfil\'.*?def perfil\(.*?\):.*?(?=@auth_bp\.route|$)'
content = re.sub(pattern, '', content, flags=re.DOTALL)

# Adicionar nova função no final
with open('/tmp/new_perfil.py', 'r') as f:
    new_perfil = f.read()

content = content.rstrip() + '\n\n' + new_perfil + '\n'

with open('routes/auth.py', 'w') as f:
    f.write(content)

print("✅ Função perfil corrigida")
EOF

echo "   ✅ routes/auth.py corrigido"

# 3. Corrigir template
echo "🎨 Corrigindo template..."

# Substituir referências ao form por HTML puro
sed -i 's/{{ form\.hidden_tag() }}//g' templates/auth/perfil.html
sed -i 's/{{ form\.senha_atual\.label(class="form-label") }}/<label for="senha_atual" class="form-label">Senha Atual<\/label>/g' templates/auth/perfil.html
sed -i 's/{{ form\.senha_atual(class="form-control") }}/<input type="password" class="form-control" id="senha_atual" name="senha_atual" placeholder="Digite sua senha atual" required>/g' templates/auth/perfil.html
sed -i 's/{{ form\.nova_senha\.label(class="form-label") }}/<label for="nova_senha" class="form-label">Nova Senha<\/label>/g' templates/auth/perfil.html
sed -i 's/{{ form\.nova_senha(class="form-control") }}/<input type="password" class="form-control" id="nova_senha" name="nova_senha" placeholder="Digite a nova senha" minlength="6" required>/g' templates/auth/perfil.html
sed -i 's/{{ form\.confirmar_nova_senha\.label(class="form-label") }}/<label for="confirmar_nova_senha" class="form-label">Confirmar Nova Senha<\/label>/g' templates/auth/perfil.html
sed -i 's/{{ form\.confirmar_nova_senha(class="form-control") }}/<input type="password" class="form-control" id="confirmar_nova_senha" name="confirmar_nova_senha" placeholder="Digite a nova senha novamente" minlength="6" required>/g' templates/auth/perfil.html
sed -i 's/{{ form\.submit(class="btn btn-primary") }}/<button type="submit" class="btn btn-primary"><i class="fas fa-key me-2"><\/i>Alterar Senha<\/button>/g' templates/auth/perfil.html

# Remover loops de erro do form
sed -i '/{% for error in form\./,/{% endfor %}/d' templates/auth/perfil.html

echo "   ✅ Template corrigido"

# 4. Verificar sintaxe
echo "🧪 Verificando sintaxe..."
if python3 -m py_compile routes/auth.py; then
    echo "   ✅ Sintaxe OK"
else
    echo "   ❌ Erro de sintaxe, restaurando backup"
    cp routes/auth.py.emergency_backup routes/auth.py
    cp templates/auth/perfil.html.emergency_backup templates/auth/perfil.html
    exit 1
fi

# 5. Reiniciar serviço
echo "🔄 Reiniciando serviço..."
supervisorctl restart assessment
sleep 3

# 6. Testar
echo "🧪 Testando rota..."
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/perfil)

if [ "$response_code" = "200" ] || [ "$response_code" = "302" ]; then
    echo "   ✅ Rota funcionando (código: $response_code)"
    echo ""
    echo "🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!"
    echo "   Teste agora: http://seu-servidor:8000/auth/perfil"
else
    echo "   ⚠️  Código de resposta: $response_code"
    echo "   Verifique logs: tail -f /var/log/assessment.log"
fi

echo ""
echo "📋 ARQUIVOS DE BACKUP:"
echo "   routes/auth.py.emergency_backup"
echo "   templates/auth/perfil.html.emergency_backup"