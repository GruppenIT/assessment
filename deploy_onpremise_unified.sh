#!/bin/bash
# Sistema de Avaliações de Maturidade - Deploy Unificado On-Premise
# Atualiza código do Git preservando dados existentes (projetos, clientes, usuários, assessments)

set -e  # Parar execução em caso de erro

echo "🚀 SISTEMA DE AVALIAÇÕES DE MATURIDADE - DEPLOY ON-PREMISE"
echo "========================================================="
echo "⚠️  ESTE SCRIPT PRESERVA TODOS OS DADOS EXISTENTES"
echo "   • Projetos, Clientes, Usuários e Assessments são mantidos"
echo "   • Backup completo é criado antes da atualização"
echo ""

# Verificar se está executando como root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script deve ser executado como root (sudo)"
   exit 1
fi

# Configurações
INSTALL_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment_backups"
GIT_REPO="https://github.com/GruppenIT/assessment.git"
SERVICE_NAME="assessment"
VENV_DIR="$INSTALL_DIR/venv"
LOG_FILE="/var/log/assessment_deploy.log"

# Função para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Função para backup completo
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$timestamp"
    
    log "📋 Criando backup completo..."
    mkdir -p "$backup_path"
    
    # Backup do código fonte
    if [ -d "$INSTALL_DIR" ]; then
        cp -r "$INSTALL_DIR" "$backup_path/code"
        log "   ✅ Código fonte copiado"
    fi
    
    # Backup do banco de dados PostgreSQL
    log "   💾 Fazendo backup do banco de dados..."
    if sudo -u postgres pg_dump assessment_db > "$backup_path/database_backup.sql" 2>/dev/null; then
        log "   ✅ Backup do banco criado: $backup_path/database_backup.sql"
    else
        log "   ⚠️  Não foi possível fazer backup do banco (pode não existir ainda)"
    fi
    
    # Backup da configuração do Supervisor
    if [ -f "/etc/supervisor/conf.d/assessment.conf" ]; then
        cp "/etc/supervisor/conf.d/assessment.conf" "$backup_path/"
        log "   ✅ Configuração Supervisor copiada"
    fi
    
    # Backup do arquivo .env se existir
    if [ -f "$INSTALL_DIR/.env" ]; then
        cp "$INSTALL_DIR/.env" "$backup_path/"
        log "   ✅ Arquivo .env copiado"
    fi
    
    echo "$backup_path" > /tmp/last_backup_path
    log "✅ Backup completo criado em: $backup_path"
}

# Função para verificar mudanças na estrutura do banco
check_database_changes() {
    log "🔍 Verificando mudanças na estrutura do banco..."
    
    local models_file="$INSTALL_DIR/models.py"
    local init_db_file="$INSTALL_DIR/init_db.py"
    
    if [ -f "$models_file" ]; then
        # Verificar se há novas tabelas ou mudanças significativas
        local new_tables=$(grep -c "class.*db.Model" "$models_file" 2>/dev/null || echo "0")
        log "   📊 Encontradas $new_tables classes de modelo no código"
        
        # Verificar por palavras-chave que indicam mudanças estruturais
        if grep -q "db.Column.*nullable=False" "$models_file" 2>/dev/null; then
            log "   ⚠️  ATENÇÃO: Detectadas colunas NOT NULL que podem causar problemas"
            log "   📋 Recomendação: Revisar models.py antes de continuar"
        fi
        
        if grep -q "db.drop_all\|DROP TABLE\|ALTER TABLE.*DROP" "$models_file" "$init_db_file" 2>/dev/null; then
            echo ""
            echo "🚨 ALERTA CRÍTICO: DETECTADAS OPERAÇÕES DESTRUTIVAS NO BANCO"
            echo "   • DROP TABLE, DROP COLUMN ou db.drop_all() encontrados"
            echo "   • Estas operações podem APAGAR DADOS EXISTENTES"
            echo ""
            read -p "⚠️  Deseja continuar mesmo assim? (digite 'SIM' para confirmar): " confirm
            if [ "$confirm" != "SIM" ]; then
                log "❌ Deploy cancelado pelo usuário devido a operações destrutivas"
                exit 1
            fi
        fi
    fi
}

# Função para parar serviços
stop_services() {
    log "🛑 Parando serviços..."
    if systemctl is-active --quiet supervisor; then
        supervisorctl stop "$SERVICE_NAME" 2>/dev/null || true
        log "   ✅ Serviço $SERVICE_NAME parado"
    fi
}

# Função para inicializar ou atualizar código
update_code() {
    log "📥 Atualizando código fonte..."
    
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        log "   🌟 Primeira instalação - clonando repositório..."
        rm -rf "$INSTALL_DIR"
        git clone "$GIT_REPO" "$INSTALL_DIR"
    else
        log "   🔄 Atualizando código existente..."
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/main
    fi
    
    cd "$INSTALL_DIR"
    log "   ✅ Código atualizado para último commit: $(git rev-parse --short HEAD)"
}

# Função para configurar ambiente Python
setup_python_environment() {
    log "🐍 Configurando ambiente Python..."
    
    cd "$INSTALL_DIR"
    
    # Criar/atualizar virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log "   ✅ Virtual environment criado"
    fi
    
    # Ativar venv e instalar dependências
    source "$VENV_DIR/bin/activate"
    
    # Atualizar pip
    pip install --upgrade pip
    
    # Instalar dependências
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log "   ✅ Dependências instaladas via requirements.txt"
    fi
    
    # Verificar dependências críticas
    python3 -c "import flask, flask_sqlalchemy, flask_login" 2>/dev/null || {
        log "   ❌ Dependências críticas ausentes, tentando instalar..."
        pip install flask flask-sqlalchemy flask-login flask-wtf psycopg2-binary gunicorn
    }
    
    log "   ✅ Ambiente Python configurado"
}

# Função para aplicar correções de segurança
apply_security_fixes() {
    log "🔒 Aplicando correções de segurança..."
    
    cd "$INSTALL_DIR"
    
    # Aplicar middleware de segurança no app.py
    if ! grep -q "@app.before_request" app.py; then
        log "   🛡️  Aplicando middleware de autenticação..."
        
        # Usar Python para aplicar patch seguro
        python3 << 'EOF'
import re

# Middleware code
middleware_code = """
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

"""

try:
    with open('app.py', 'r') as f:
        content = f.read()
    
    # Procurar pelo final da função create_app (antes do return app)
    pattern = r'(\s+return app\s*\n)'
    match = re.search(pattern, content)
    
    if match:
        insert_pos = match.start()
        new_content = content[:insert_pos] + middleware_code + content[insert_pos:]
        
        with open('app.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Middleware de segurança aplicado")
    else:
        print("⚠️  Não foi possível aplicar middleware automaticamente")
        
except Exception as e:
    print(f"❌ Erro ao aplicar middleware: {e}")
EOF
    else
        log "   ℹ️  Middleware de segurança já presente"
    fi
    
    # Corrigir problemas específicos do auth.py
    log "   🔧 Aplicando correções no auth.py..."
    python3 << 'EOF'
import re

try:
    # Corrigir routes/auth.py
    with open('routes/auth.py', 'r') as f:
        content = f.read()
    
    # Remover import do AlterarSenhaForm se existir (não é mais necessário)
    content = re.sub(
        r'from forms\.auth_forms import LoginForm, AlterarSenhaForm',
        'from forms.auth_forms import LoginForm',
        content
    )
    
    # Corrigir problemas de None nos formulários
    content = re.sub(
        r'email = form\.email\.data\.lower\(\)\.strip\(\)',
        'email = form.email.data.lower().strip() if form.email.data else ""',
        content
    )
    
    content = re.sub(
        r'senha = form\.senha\.data',
        'senha = form.senha.data if form.senha.data else ""',
        content
    )
    
    # Substituir função de perfil simples pela versão com alteração de senha
    perfil_pattern = r'@auth_bp\.route\(\'/perfil\'\).*?def perfil\(\):.*?return render_template\([^)]+\)'
    
    new_perfil_function = '''@auth_bp.route('/perfil', methods=['GET', 'POST'])
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
                
                # Registrar na auditoria
                try:
                    from models.auditoria import registrar_auditoria
                    usuario_tipo = 'admin' if hasattr(current_user, 'tipo') and current_user.tipo == 'admin' else 'respondente'
                    registrar_auditoria(
                        acao='senha_alterada',
                        usuario_tipo=usuario_tipo,
                        usuario_id=current_user.id,
                        usuario_nome=current_user.nome,
                        detalhes='Senha alterada pelo próprio usuário',
                        ip_address=request.remote_addr
                    )
                except:
                    pass  # Continua mesmo se auditoria falhar
                
                flash('Senha alterada com sucesso!', 'success')
                return redirect(url_for('auth.perfil'))
                
            except Exception as e:
                db.session.rollback()
                flash('Erro ao alterar senha. Tente novamente.', 'danger')
    
    return render_template('auth/perfil.html', usuario=current_user)'''
    
    content = re.sub(perfil_pattern, new_perfil_function, content, flags=re.DOTALL)
    
    with open('routes/auth.py', 'w') as f:
        f.write(content)
    
    print("✅ Correções aplicadas em routes/auth.py")
    
except Exception as e:
    print(f"❌ Erro ao corrigir auth.py: {e}")
EOF

    # Remover AlterarSenhaForm se existir (não é mais necessário)
    log "   📝 Limpando formulários desnecessários..."
    if grep -q "AlterarSenhaForm" forms/auth_forms.py; then
        sed -i '/class AlterarSenhaForm/,/submit = SubmitField/d' forms/auth_forms.py
        log "   ✅ AlterarSenhaForm removido (usando HTML puro)"
    fi
    
    # Remover rotas de auto-login se existirem
    for route_file in routes/auth.py routes/respondente.py routes/projeto.py; do
        if [ -f "$route_file" ] && grep -q "auto.*login" "$route_file"; then
            sed -i '/auto.*login/d' "$route_file"
            log "   🗑️  Rotas de auto-login removidas de $route_file"
        fi
    done
    
    log "   ✅ Correções de segurança aplicadas"
}

# Função para corrigir template de perfil
fix_profile_template() {
    log "🎨 Corrigindo template de perfil..."
    
    cd "$INSTALL_DIR"
    
    # Corrigir template auth/perfil.html
    if [ -f "templates/auth/perfil.html" ]; then
        log "   🔧 Atualizando template de perfil..."
        
        # Backup do template original
        cp templates/auth/perfil.html templates/auth/perfil.html.backup
        
        # Aplicar correções no template usando Python
        python3 << 'EOF'
import re

try:
    with open('templates/auth/perfil.html', 'r') as f:
        content = f.read()
    
    # Corrigir verificações de tipo de usuário
    content = re.sub(
        r'current_user\.is_admin\(\)',
        "hasattr(current_user, 'tipo') and current_user.tipo == 'admin'",
        content
    )
    
    content = re.sub(
        r'current_user\.is_cliente\(\)',
        "hasattr(current_user, 'cliente_id') and current_user.cliente_id",
        content
    )
    
    # Corrigir acesso a nome_empresa
    content = re.sub(
        r'current_user\.nome_empresa',
        "current_user.cliente.nome_empresa if hasattr(current_user, 'cliente') and current_user.cliente else None",
        content
    )
    
    # Adicionar modal de alteração de senha se não existir
    if 'alterarSenhaModal' not in content:
        modal_html = '''
    <!-- Modal para Alterar Senha -->
    <div class="modal fade" id="alterarSenhaModal" tabindex="-1" aria-labelledby="alterarSenhaModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <form method="POST" action="{{ url_for('auth.perfil') }}">

                    <div class="modal-header">
                        <h5 class="modal-title" id="alterarSenhaModalLabel">
                            <i class="fas fa-key me-2"></i>
                            Alterar Senha
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="senha_atual" class="form-label">Senha Atual</label>
                            <input type="password" class="form-control" id="senha_atual" name="senha_atual" 
                                   placeholder="Digite sua senha atual" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="nova_senha" class="form-label">Nova Senha</label>
                            <input type="password" class="form-control" id="nova_senha" name="nova_senha" 
                                   placeholder="Digite a nova senha" minlength="6" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="confirmar_nova_senha" class="form-label">Confirmar Nova Senha</label>
                            <input type="password" class="form-control" id="confirmar_nova_senha" name="confirmar_nova_senha" 
                                   placeholder="Digite a nova senha novamente" minlength="6" required>
                        </div>
                        
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            A nova senha deve ter pelo menos 6 caracteres.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-2"></i>
                            Cancelar
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-key me-2"></i>
                            Alterar Senha
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>'''
        
        # Inserir modal antes do {% endblock %}
        content = content.replace('{% endblock %}', modal_html + '\n{% endblock %}')
        
        # Adicionar botão de alterar senha se não existir
        if 'Alterar Senha' not in content:
            # Procurar pela seção de botões e adicionar botão de alterar senha
            button_pattern = r'(<hr>\s*<a href="{{ url_for\(\'auth\.logout\'\) }}")'
            replacement = r'''<button type="button" class="btn btn-outline-warning" data-bs-toggle="modal" data-bs-target="#alterarSenhaModal">
                            <i class="fas fa-key me-2"></i>
                            Alterar Senha
                        </button>
                        
                        \1'''
            content = re.sub(button_pattern, replacement, content)
    
    with open('templates/auth/perfil.html', 'w') as f:
        f.write(content)
    
    print("✅ Template de perfil corrigido")
    
except Exception as e:
    print(f"❌ Erro ao corrigir template: {e}")
EOF
        
        log "   ✅ Template de perfil atualizado"
    else
        log "   ⚠️  Template de perfil não encontrado"
    fi
}

# Função para configurar banco de dados
setup_database() {
    log "💾 Configurando banco de dados..."
    
    cd "$INSTALL_DIR"
    
    # Verificar se PostgreSQL está rodando
    if ! systemctl is-active --quiet postgresql; then
        log "   🔄 Iniciando PostgreSQL..."
        systemctl start postgresql
    fi
    
    # Criar banco se não existir (preservando dados existentes)
    sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw assessment_db || {
        log "   🌟 Criando banco assessment_db..."
        sudo -u postgres createdb assessment_db
    }
    
    # Executar init_db.py apenas se for primeira instalação
    if [ -f "init_db.py" ]; then
        source "$VENV_DIR/bin/activate"
        
        # Verificar se já existem dados (tabela usuarios)
        if sudo -u postgres psql -d assessment_db -c "\dt" 2>/dev/null | grep -q "usuario\|users"; then
            log "   ℹ️  Banco de dados já contém dados, pulando inicialização"
        else
            log "   🔧 Inicializando estrutura do banco..."
            python3 init_db.py
        fi
    fi
    
    log "   ✅ Banco de dados configurado"
}

# Função para configurar Supervisor
setup_supervisor() {
    log "⚙️  Configurando Supervisor..."
    
    # Criar configuração do Supervisor
    cat > /etc/supervisor/conf.d/assessment.conf << EOF
[program:assessment]
directory=$INSTALL_DIR
command=$VENV_DIR/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 50 --reuse-port --reload wsgi:app
autostart=true
autorestart=true
stderr_logfile=/var/log/assessment_error.log
stdout_logfile=/var/log/assessment.log
user=www-data
environment=PATH="$VENV_DIR/bin"
EOF

    # Recarregar configuração do Supervisor
    supervisorctl reread
    supervisorctl update
    
    log "   ✅ Supervisor configurado"
}

# Função para definir permissões
set_permissions() {
    log "🔐 Configurando permissões..."
    
    chown -R www-data:www-data "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    
    # Permissões especiais para diretórios sensíveis
    if [ -d "$INSTALL_DIR/uploads" ]; then
        chmod 750 "$INSTALL_DIR/uploads"
    fi
    
    log "   ✅ Permissões configuradas"
}

# Função para iniciar serviços
start_services() {
    log "🔄 Iniciando serviços..."
    
    systemctl enable supervisor
    systemctl start supervisor
    
    supervisorctl start "$SERVICE_NAME"
    sleep 3
    
    # Verificar se está rodando
    if supervisorctl status "$SERVICE_NAME" | grep -q "RUNNING"; then
        log "   ✅ Serviço $SERVICE_NAME iniciado com sucesso"
    else
        log "   ❌ Falha ao iniciar serviço, verificando logs..."
        supervisorctl tail "$SERVICE_NAME"
        return 1
    fi
}

# Função para verificar deploy
verify_deployment() {
    log "🔍 Verificando deployment..."
    
    # Aguardar alguns segundos para o serviço inicializar
    sleep 5
    
    # Testar se está respondendo
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/login)
    
    if [ "$response_code" = "200" ]; then
        log "   ✅ Aplicação respondendo corretamente (código $response_code)"
    else
        log "   ⚠️  Aplicação retornou código $response_code"
    fi
    
    # Testar segurança
    local protected_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/dashboard)
    
    if [ "$protected_response" = "302" ]; then
        log "   ✅ Proteção de segurança ativa (redirecionamento para login)"
    else
        log "   ⚠️  Segurança pode não estar funcionando (código $protected_response)"
    fi
}

# Função principal
main() {
    log "🚀 Iniciando deploy unificado..."
    
    # 1. Criar backup completo
    create_backup
    
    # 2. Verificar mudanças potencialmente perigosas
    if [ -d "$INSTALL_DIR" ]; then
        check_database_changes
    fi
    
    # 3. Parar serviços
    stop_services
    
    # 4. Atualizar código
    update_code
    
    # 5. Configurar ambiente Python
    setup_python_environment
    
    # 6. Aplicar correções de segurança e bugs
    apply_security_fixes
    
    # 6.1. Corrigir template de perfil
    fix_profile_template
    
    # 7. Configurar banco de dados (preservando dados)
    setup_database
    
    # 8. Configurar Supervisor
    setup_supervisor
    
    # 9. Definir permissões
    set_permissions
    
    # 10. Iniciar serviços
    start_services
    
    # 11. Verificar deployment
    verify_deployment
    
    log "✅ DEPLOY CONCLUÍDO COM SUCESSO!"
    
    echo ""
    echo "🎉 SISTEMA ATUALIZADO E OPERACIONAL!"
    echo "=================================="
    echo "🌐 Aplicação disponível em: http://$(hostname -I | awk '{print $1}'):8000"
    echo "📋 Logs em: /var/log/assessment.log"
    echo "💾 Backup em: $(cat /tmp/last_backup_path 2>/dev/null || echo 'N/A')"
    echo ""
    echo "📊 Status dos serviços:"
    supervisorctl status "$SERVICE_NAME"
    echo ""
    echo "🔧 Comandos úteis:"
    echo "   • Ver logs: sudo tail -f /var/log/assessment.log"
    echo "   • Status: sudo supervisorctl status assessment"
    echo "   • Reiniciar: sudo supervisorctl restart assessment"
    echo ""
    
    # Limpar arquivo temporário
    rm -f /tmp/last_backup_path
}

# Executar função principal
main "$@"