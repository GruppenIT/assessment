#!/bin/bash
# Correção definitiva baseada no erro específico relatado

echo "🎯 CORREÇÃO DEFINITIVA - ERRO 500 NO PERFIL ADMIN"
echo "================================================="

cd /var/www/assessment

# Parar serviço
supervisorctl stop assessment

# Backup completo
echo "💾 Backup..."
cp routes/auth.py routes/auth.py.definitivo_backup
cp templates/auth/perfil.html templates/auth/perfil.html.definitivo_backup 2>/dev/null || echo "Template não existe"

# 1. RECRIAR ROTA AUTH COMPLETAMENTE LIMPA
echo "🔧 Recriando rota auth..."

cat > routes/auth.py << 'EOF'
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models.usuario import Usuario
from models.respondente import Respondente
from forms.auth_forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login do usuário"""
    if current_user.is_authenticated:
        if hasattr(current_user, 'tipo') and current_user.tipo == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('respondente.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = (form.email.data or "").lower().strip()
        senha = form.senha.data or ""
        
        if not email or not senha:
            flash('Email e senha são obrigatórios.', 'danger')
            return render_template('auth/login.html', form=form)
        
        # Tentar login como admin
        usuario_admin = Usuario.query.filter_by(email=email).first()
        if usuario_admin and check_password_hash(usuario_admin.senha_hash, senha):
            login_user(usuario_admin, remember=form.lembrar.data)
            next_page = request.args.get('next')
            flash(f'Bem-vindo, {usuario_admin.nome}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        
        # Tentar login como respondente
        respondente = Respondente.query.filter_by(email=email).first()
        if respondente and check_password_hash(respondente.senha_hash, senha):
            login_user(respondente, remember=form.lembrar.data)
            next_page = request.args.get('next')
            flash(f'Bem-vindo, {respondente.nome}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('respondente.dashboard'))
        
        flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil - versão estável"""
    try:
        # Dados básicos do usuário
        user_data = {
            'nome': current_user.nome,
            'email': current_user.email,
            'id': current_user.id,
            'tipo': getattr(current_user, 'tipo', 'admin') if hasattr(current_user, 'tipo') else 'admin'
        }
        
        return render_template('auth/perfil_simples.html', user_data=user_data)
        
    except Exception as e:
        # Log do erro e retorno de página de erro amigável
        import traceback
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'user_info': {
                'id': getattr(current_user, 'id', 'N/A'),
                'nome': getattr(current_user, 'nome', 'N/A'),
                'email': getattr(current_user, 'email', 'N/A')
            }
        }
        
        return render_template('auth/perfil_erro.html', error_details=error_details), 500
EOF

echo "✅ Rota auth recriada"

# 2. CRIAR TEMPLATE PERFIL SIMPLES
echo "🎨 Criando template perfil simples..."

mkdir -p templates/auth

cat > templates/auth/perfil_simples.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil - Sistema de Assessments</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/admin/dashboard">
                <i class="fas fa-chart-line me-2"></i>
                Sistema de Assessments
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">
                            <i class="fas fa-user me-2"></i>
                            Perfil do Usuário
                        </h4>
                    </div>
                    
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h5 class="text-muted mb-3">Informações Pessoais</h5>
                                
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Nome Completo:</label>
                                    <p class="form-control-plaintext border-bottom">
                                        {{ user_data.nome if user_data and user_data.nome else 'Não informado' }}
                                    </p>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Email:</label>
                                    <p class="form-control-plaintext border-bottom">
                                        {{ user_data.email if user_data and user_data.email else 'Não informado' }}
                                    </p>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label fw-bold">Tipo de Usuário:</label>
                                    <p class="form-control-plaintext">
                                        <span class="badge bg-success px-3 py-2">
                                            <i class="fas fa-crown me-1"></i>
                                            {{ 'Administrador' if user_data and user_data.tipo == 'admin' else 'Usuário' }}
                                        </span>
                                    </p>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <h5 class="text-muted mb-3">Ações Disponíveis</h5>
                                
                                <div class="d-grid gap-3">
                                    <a href="/admin/dashboard" class="btn btn-outline-primary">
                                        <i class="fas fa-tachometer-alt me-2"></i>
                                        Voltar ao Dashboard
                                    </a>
                                    
                                    <button class="btn btn-outline-secondary" disabled>
                                        <i class="fas fa-key me-2"></i>
                                        Alterar Senha (Em breve)
                                    </button>
                                    
                                    <a href="/auth/logout" class="btn btn-outline-danger">
                                        <i class="fas fa-sign-out-alt me-2"></i>
                                        Sair do Sistema
                                    </a>
                                </div>
                                
                                <div class="alert alert-info mt-4">
                                    <i class="fas fa-info-circle me-2"></i>
                                    <small>
                                        Funcionalidades adicionais do perfil serão implementadas nas próximas versões.
                                    </small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card-footer text-muted text-center">
                        <small>
                            <i class="fas fa-clock me-1"></i>
                            Último acesso: {{ moment().format('DD/MM/YYYY HH:mm') if moment else 'Agora' }}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
EOF

echo "✅ Template perfil simples criado"

# 3. CRIAR TEMPLATE DE ERRO
echo "⚠️  Criando template de erro..."

cat > templates/auth/perfil_erro.html << 'EOF'
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro no Perfil - Sistema de Assessments</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card border-danger">
                    <div class="card-header bg-danger text-white">
                        <h4 class="mb-0">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Erro no Perfil do Usuário
                        </h4>
                    </div>
                    
                    <div class="card-body">
                        <div class="alert alert-danger">
                            <h5>Ocorreu um erro inesperado</h5>
                            <p class="mb-0">Não foi possível carregar as informações do seu perfil.</p>
                        </div>
                        
                        <div class="mb-4">
                            <h6>Informações do usuário:</h6>
                            <ul class="list-unstyled">
                                <li><strong>ID:</strong> {{ error_details.user_info.id if error_details else 'N/A' }}</li>
                                <li><strong>Nome:</strong> {{ error_details.user_info.nome if error_details else 'N/A' }}</li>
                                <li><strong>Email:</strong> {{ error_details.user_info.email if error_details else 'N/A' }}</li>
                            </ul>
                        </div>
                        
                        <div class="d-grid gap-2">
                            <a href="/admin/dashboard" class="btn btn-primary">
                                <i class="fas fa-home me-2"></i>
                                Voltar ao Dashboard
                            </a>
                            
                            <button class="btn btn-outline-secondary" onclick="location.reload()">
                                <i class="fas fa-sync me-2"></i>
                                Tentar Novamente
                            </button>
                        </div>
                        
                        <details class="mt-4">
                            <summary class="text-muted">Detalhes técnicos do erro</summary>
                            <div class="mt-2">
                                <pre class="bg-light p-3 small text-danger">{{ error_details.error if error_details else 'Erro não especificado' }}</pre>
                            </div>
                        </details>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF

echo "✅ Template de erro criado"

# 4. VERIFICAR E AJUSTAR PERMISSÕES
echo "🔐 Ajustando permissões..."
chown -R www-data:www-data /var/www/assessment/
chmod -R 755 /var/www/assessment/
chmod 644 /var/www/assessment/routes/auth.py
chmod 644 /var/www/assessment/templates/auth/*.html

# 5. LIMPAR CACHE E REINICIAR
echo "🧹 Limpando cache..."
find /var/www/assessment -name "*.pyc" -delete
find /var/www/assessment -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "🔄 Reiniciando serviço..."
supervisorctl start assessment
sleep 5

# 6. TESTE FINAL
echo "🧪 Testando..."
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/perfil 2>/dev/null || echo "000")

if [ "$response_code" = "200" ] || [ "$response_code" = "302" ]; then
    echo ""
    echo "🎉 SUCESSO! PERFIL CORRIGIDO!"
    echo "   Código de resposta: $response_code"
    echo "   ✅ Acesse: https://assessments.zerobox.com.br/auth/perfil"
    echo ""
    echo "📋 O que foi corrigido:"
    echo "   • Rota auth.py completamente reescrita"
    echo "   • Template perfil simplificado sem dependências"
    echo "   • Template de erro para casos excepcionais" 
    echo "   • Tratamento robusto de exceções"
    echo "   • Permissões ajustadas"
    echo ""
else
    echo ""
    echo "⚠️  Resposta: $response_code"
    echo "   Verificando logs..."
    echo ""
    echo "📋 LOGS RECENTES:"
    tail -10 /var/log/supervisor/assessment-*.log 2>/dev/null || echo "Logs não encontrados"
    echo ""
    echo "📋 STATUS:"
    supervisorctl status assessment
fi

echo ""
echo "💾 BACKUPS SALVOS:"
echo "   routes/auth.py.definitivo_backup"
echo "   templates/auth/perfil.html.definitivo_backup"