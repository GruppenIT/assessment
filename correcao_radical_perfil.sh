#!/bin/bash
# Correção radical para o problema do perfil on-premise

echo "🚨 CORREÇÃO RADICAL - PERFIL ON-PREMISE"
echo "======================================"

cd /var/www/assessment

# Parar serviço
echo "⏹️  Parando serviço..."
supervisorctl stop assessment

# Backup completo
echo "💾 Backup completo..."
mkdir -p /tmp/backup_$(date +%Y%m%d_%H%M%S)
cp -r routes/ forms/ templates/ /tmp/backup_$(date +%Y%m%d_%H%M%S)/

# 1. RECRIAR COMPLETAMENTE A ROTA AUTH
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
        email = form.email.data.lower().strip() if form.email.data else ""
        senha = form.senha.data if form.senha.data else ""
        
        if not email or not senha:
            flash('Email e senha são obrigatórios.', 'danger')
            return render_template('auth/login.html', form=form)
        
        # Tentar login como admin
        usuario_admin = Usuario.query.filter_by(email=email).first()
        if usuario_admin and check_password_hash(usuario_admin.senha_hash, senha):
            login_user(usuario_admin, remember=form.lembrar.data)
            next_page = request.args.get('next')
            
            try:
                from models.auditoria import registrar_login
                registrar_login(
                    usuario_tipo='admin',
                    usuario_id=usuario_admin.id,
                    usuario_nome=usuario_admin.nome,
                    usuario_email=usuario_admin.email
                )
            except:
                pass
            
            flash(f'Bem-vindo, {usuario_admin.nome}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        
        # Tentar login como respondente
        respondente = Respondente.query.filter_by(email=email).first()
        if respondente and check_password_hash(respondente.senha_hash, senha):
            login_user(respondente, remember=form.lembrar.data)
            next_page = request.args.get('next')
            
            try:
                from models.auditoria import registrar_login
                registrar_login(
                    usuario_tipo='respondente',
                    usuario_id=respondente.id,
                    usuario_nome=respondente.nome,
                    usuario_email=respondente.email
                )
            except:
                pass
            
            flash(f'Bem-vindo, {respondente.nome}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('respondente.dashboard'))
        
        flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    try:
        from models.auditoria import registrar_logout
        
        if current_user.is_authenticated:
            usuario_tipo = 'admin' if hasattr(current_user, 'tipo') and current_user.tipo == 'admin' else 'respondente'
            usuario_nome = getattr(current_user, 'nome', 'Usuário')
            usuario_email = getattr(current_user, 'email', None)
            
            registrar_logout(
                usuario_tipo=usuario_tipo,
                usuario_id=current_user.id,
                usuario_nome=usuario_nome,
                usuario_email=usuario_email
            )
    except:
        pass
    
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Página de perfil simplificada - SEM alteração de senha por enquanto"""
    
    if request.method == 'POST':
        flash('Funcionalidade de alteração de senha temporariamente desabilitada.', 'info')
    
    return render_template('auth/perfil.html', usuario=current_user)
EOF

echo "✅ Rota auth recriada"

# 2. RECRIAR TEMPLATE SIMPLIFICADO
echo "🎨 Recriando template..."

cat > templates/auth/perfil.html << 'EOF'
{% extends "base.html" %}

{% block title %}Perfil do Usuário{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">
                        <i class="fas fa-user me-2"></i>
                        Perfil do Usuário
                    </h5>
                </div>
                
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-muted">Informações Básicas</h6>
                            
                            <div class="mb-3">
                                <label class="form-label fw-bold">Nome:</label>
                                <p class="form-control-plaintext">{{ usuario.nome }}</p>
                            </div>
                            
                            <div class="mb-3">
                                <label class="form-label fw-bold">Email:</label>
                                <p class="form-control-plaintext">{{ usuario.email }}</p>
                            </div>
                            
                            {% if hasattr(usuario, 'tipo') %}
                            <div class="mb-3">
                                <label class="form-label fw-bold">Tipo:</label>
                                <p class="form-control-plaintext">
                                    <span class="badge bg-primary">
                                        {{ 'Administrador' if usuario.tipo == 'admin' else 'Respondente' }}
                                    </span>
                                </p>
                            </div>
                            {% endif %}
                        </div>
                        
                        <div class="col-md-6">
                            <h6 class="text-muted">Ações</h6>
                            
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                A funcionalidade de alteração de senha será implementada em breve.
                            </div>
                            
                            <div class="d-grid gap-2">
                                <a href="{{ url_for('admin.dashboard') if hasattr(usuario, 'tipo') and usuario.tipo == 'admin' else url_for('respondente.dashboard') }}" 
                                   class="btn btn-secondary">
                                    <i class="fas fa-arrow-left me-2"></i>
                                    Voltar ao Dashboard
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

echo "✅ Template recriado"

# 3. VERIFICAR FORMS
echo "🔍 Verificando forms..."

if [ ! -f "forms/auth_forms.py" ]; then
    echo "❌ forms/auth_forms.py não existe, criando..."
    mkdir -p forms
    cat > forms/auth_forms.py << 'EOF'
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    """Formulário de login"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ], render_kw={'placeholder': 'Digite seu email'})
    
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ], render_kw={'placeholder': 'Digite sua senha'})
    
    lembrar = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')
EOF
fi

# 4. VERIFICAR SINTAXE
echo "🧪 Verificando sintaxe..."
if ! python3 -m py_compile routes/auth.py; then
    echo "❌ Erro de sintaxe em auth.py"
    exit 1
fi

if ! python3 -m py_compile forms/auth_forms.py; then
    echo "❌ Erro de sintaxe em forms/auth_forms.py"
    exit 1
fi

echo "✅ Sintaxe OK"

# 5. VERIFICAR PERMISSÕES
echo "🔐 Ajustando permissões..."
chown -R www-data:www-data /var/www/assessment/
chmod -R 755 /var/www/assessment/

# 6. LIMPAR CACHE PYTHON
echo "🧹 Limpando cache..."
find /var/www/assessment -name "*.pyc" -delete
find /var/www/assessment -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 7. REINICIAR SERVIÇOS
echo "🔄 Reiniciando serviços..."
supervisorctl start assessment
sleep 5

# 8. TESTAR
echo "🧪 Testando..."
sleep 3

# Teste básico
response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/perfil 2>/dev/null || echo "000")

if [ "$response_code" = "200" ] || [ "$response_code" = "302" ]; then
    echo "✅ CORREÇÃO BEM-SUCEDIDA!"
    echo "   Código de resposta: $response_code"
    echo "   Teste: http://seu-servidor:8000/auth/perfil"
else
    echo "❌ Problema persiste (código: $response_code)"
    echo "   Verificando logs..."
    
    # Mostrar logs recentes
    echo ""
    echo "📋 LOGS RECENTES:"
    tail -20 /var/log/supervisor/assessment-*.log 2>/dev/null || echo "Logs não encontrados"
    
    echo ""
    echo "📋 STATUS DO SERVIÇO:"
    supervisorctl status assessment
fi

echo ""
echo "📂 BACKUP CRIADO EM: /tmp/backup_$(date +%Y%m%d_%H%M%S)/"
echo "🔧 Para reverter: cp -r /tmp/backup_*/routes/* routes/"