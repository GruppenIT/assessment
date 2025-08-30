#!/usr/bin/env python3
"""
Diagnóstico específico para erro 500 na rota /auth/perfil quando logado como admin
"""

import os
import sys
import traceback
import subprocess
import time
from datetime import datetime

def create_test_route():
    """Criar rota de teste isolada para diagnosticar o problema"""
    print("🔧 Criando rota de teste isolada...")
    
    test_route = '''
@auth_bp.route('/perfil-test')
@login_required  
def perfil_test():
    """Rota de teste para diagnosticar problema do perfil"""
    try:
        # Log de debug
        print(f"[DEBUG] Usuario atual: {current_user}")
        print(f"[DEBUG] Usuario autenticado: {current_user.is_authenticated}")
        print(f"[DEBUG] Usuario ID: {current_user.id}")
        print(f"[DEBUG] Usuario nome: {current_user.nome}")
        print(f"[DEBUG] Usuario email: {current_user.email}")
        
        if hasattr(current_user, 'tipo'):
            print(f"[DEBUG] Usuario tipo: {current_user.tipo}")
        else:
            print(f"[DEBUG] Usuario não tem atributo 'tipo'")
        
        # Teste simples de template
        return f"""
        <html>
        <head><title>Teste Perfil</title></head>
        <body>
            <h1>Teste de Perfil - OK</h1>
            <p>Usuario: {current_user.nome}</p>
            <p>Email: {current_user.email}</p>
            <p>ID: {current_user.id}</p>
            <p>Tipo: {getattr(current_user, 'tipo', 'Nao tem tipo')}</p>
            <p>Timestamp: {datetime.now()}</p>
        </body>
        </html>
        """
        
    except Exception as e:
        print(f"[ERROR] Erro na rota teste: {e}")
        traceback.print_exc()
        return f"<h1>Erro: {e}</h1><pre>{traceback.format_exc()}</pre>"
'''
    
    # Adicionar rota de teste ao auth.py
    with open('/var/www/assessment/routes/auth.py', 'r') as f:
        content = f.read()
    
    if 'perfil-test' not in content:
        content = content.rstrip() + '\n\n' + test_route + '\n'
        
        with open('/var/www/assessment/routes/auth.py', 'w') as f:
            f.write(content)
        
        print("✅ Rota de teste adicionada: /auth/perfil-test")
        return True
    
    print("ℹ️  Rota de teste já existe")
    return True

def monitor_logs_realtime():
    """Monitorar logs em tempo real enquanto acessa a rota"""
    print("📊 Monitorando logs em tempo real...")
    print("   Acesse agora: https://assessments.zerobox.com.br/auth/perfil-test")
    print("   Pressione Ctrl+C para parar o monitoramento")
    
    try:
        # Monitorar múltiplos logs simultaneamente
        cmd = """
        tail -f /var/log/supervisor/assessment-*.log \
             /var/log/assessment.log \
             /var/log/nginx/error.log \
             /var/log/nginx/access.log 2>/dev/null | \
        while read line; do
            echo "[$(date '+%H:%M:%S')] $line"
        done
        """
        
        subprocess.run(cmd, shell=True)
        
    except KeyboardInterrupt:
        print("\n✅ Monitoramento interrompido")

def create_detailed_perfil_route():
    """Criar versão detalhada da rota perfil com logging extensivo"""
    print("🔧 Criando rota perfil com logging detalhado...")
    
    detailed_route = '''
@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Página de perfil com logging detalhado para debug"""
    import logging
    import traceback
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    try:
        logger.info(f"[PERFIL] Iniciando rota perfil - {datetime.now()}")
        logger.info(f"[PERFIL] Current user: {current_user}")
        logger.info(f"[PERFIL] User authenticated: {current_user.is_authenticated}")
        logger.info(f"[PERFIL] User ID: {current_user.id}")
        logger.info(f"[PERFIL] Request method: {request.method}")
        
        # Verificar atributos do usuário
        user_attrs = dir(current_user)
        logger.info(f"[PERFIL] User attributes: {[attr for attr in user_attrs if not attr.startswith('_')]}")
        
        # Processar POST se necessário
        if request.method == 'POST':
            logger.info(f"[PERFIL] POST data: {request.form.to_dict()}")
            flash('POST recebido com sucesso (funcionalidade desabilitada temporariamente)', 'info')
        
        # Preparar dados para template
        template_data = {
            'usuario': current_user,
            'debug_info': {
                'timestamp': datetime.now(),
                'user_id': current_user.id,
                'user_name': current_user.nome,
                'user_email': current_user.email,
                'user_type': getattr(current_user, 'tipo', 'Sem tipo definido'),
                'is_authenticated': current_user.is_authenticated
            }
        }
        
        logger.info(f"[PERFIL] Template data prepared: {template_data}")
        logger.info(f"[PERFIL] Renderizando template...")
        
        # Renderizar template
        result = render_template('auth/perfil.html', **template_data)
        logger.info(f"[PERFIL] Template renderizado com sucesso")
        return result
        
    except Exception as e:
        logger.error(f"[PERFIL] ERRO: {e}")
        logger.error(f"[PERFIL] Traceback: {traceback.format_exc()}")
        
        # Retornar página de erro personalizada
        return f"""
        <html>
        <head><title>Erro no Perfil</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">Erro no Perfil</h1>
            <h2>Detalhes do Erro:</h2>
            <p><strong>Erro:</strong> {str(e)}</p>
            <h2>Informações de Debug:</h2>
            <p><strong>Usuário:</strong> {current_user.nome if current_user else 'Não logado'}</p>
            <p><strong>Email:</strong> {current_user.email if current_user else 'N/A'}</p>
            <p><strong>Timestamp:</strong> {datetime.now()}</p>
            <h2>Traceback:</h2>
            <pre style="background: #f5f5f5; padding: 10px;">{traceback.format_exc()}</pre>
            <p><a href="/admin/dashboard">← Voltar ao Dashboard</a></p>
        </body>
        </html>
        """, 500
'''
    
    # Substituir rota perfil existente
    with open('/var/www/assessment/routes/auth.py', 'r') as f:
        content = f.read()
    
    # Fazer backup
    with open('/var/www/assessment/routes/auth.py.debug_backup', 'w') as f:
        f.write(content)
    
    # Remover rota perfil existente e adicionar nova
    import re
    content = re.sub(
        r'@auth_bp\.route\(\'/perfil\'.*?def perfil\(.*?\):.*?(?=@auth_bp\.route|$)',
        detailed_route.strip(),
        content,
        flags=re.DOTALL
    )
    
    with open('/var/www/assessment/routes/auth.py', 'w') as f:
        f.write(content)
    
    print("✅ Rota perfil com logging detalhado criada")

def create_simple_perfil_template():
    """Criar template perfil ultra-simples"""
    print("🎨 Criando template perfil simplificado...")
    
    simple_template = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil do Usuário</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h4>Perfil do Usuário</h4>
                    </div>
                    <div class="card-body">
                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ 'danger' if category == 'error' else category }}">
                                        {{ message }}
                                    </div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}
                        
                        <div class="mb-3">
                            <label class="form-label"><strong>Nome:</strong></label>
                            <p class="form-control-plaintext">{{ usuario.nome if usuario else 'N/A' }}</p>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label"><strong>Email:</strong></label>
                            <p class="form-control-plaintext">{{ usuario.email if usuario else 'N/A' }}</p>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label"><strong>Tipo:</strong></label>
                            <p class="form-control-plaintext">
                                {{ usuario.tipo if usuario and hasattr(usuario, 'tipo') else 'Administrador' }}
                            </p>
                        </div>
                        
                        {% if debug_info %}
                        <details>
                            <summary>Informações de Debug</summary>
                            <div class="mt-3">
                                <small class="text-muted">
                                    <p><strong>ID:</strong> {{ debug_info.user_id }}</p>
                                    <p><strong>Autenticado:</strong> {{ debug_info.is_authenticated }}</p>
                                    <p><strong>Timestamp:</strong> {{ debug_info.timestamp }}</p>
                                </small>
                            </div>
                        </details>
                        {% endif %}
                        
                        <div class="mt-4">
                            <a href="/admin/dashboard" class="btn btn-secondary">← Voltar ao Dashboard</a>
                        </div>
                        
                        <div class="alert alert-info mt-3">
                            <small>Funcionalidade de alteração de senha temporariamente desabilitada durante debug.</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    # Fazer backup do template original
    if os.path.exists('/var/www/assessment/templates/auth/perfil.html'):
        subprocess.run(['cp', '/var/www/assessment/templates/auth/perfil.html', 
                       '/var/www/assessment/templates/auth/perfil.html.debug_backup'], check=False)
    
    # Criar template simples
    os.makedirs('/var/www/assessment/templates/auth', exist_ok=True)
    with open('/var/www/assessment/templates/auth/perfil.html', 'w') as f:
        f.write(simple_template)
    
    print("✅ Template perfil simplificado criado")

def restart_and_test():
    """Reiniciar serviço e fazer teste"""
    print("🔄 Reiniciando serviço...")
    
    # Limpar cache Python
    subprocess.run(['find', '/var/www/assessment', '-name', '*.pyc', '-delete'], check=False)
    subprocess.run(['find', '/var/www/assessment', '-name', '__pycache__', '-type', 'd', '-exec', 'rm', '-rf', '{}', '+'], 
                  check=False, stderr=subprocess.DEVNULL)
    
    # Reiniciar
    subprocess.run(['supervisorctl', 'restart', 'assessment'], check=False)
    time.sleep(5)
    
    # Teste básico
    result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
                            'http://localhost:8000/auth/perfil-test'], 
                           capture_output=True, text=True)
    
    print(f"🧪 Teste rota /auth/perfil-test: {result.stdout}")
    
    result2 = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
                             'http://localhost:8000/auth/perfil'], 
                            capture_output=True, text=True)
    
    print(f"🧪 Teste rota /auth/perfil: {result2.stdout}")

def main():
    """Função principal"""
    print("🚨 DIAGNÓSTICO ESPECÍFICO - ERRO 500 NO PERFIL ADMIN")
    print("="*60)
    
    if not os.path.exists('/var/www/assessment'):
        print("❌ Executar no servidor on-premise (/var/www/assessment)")
        return
    
    os.chdir('/var/www/assessment')
    
    print("\n1. Criando rota de teste...")
    create_test_route()
    
    print("\n2. Criando rota perfil com logging...")
    create_detailed_perfil_route()
    
    print("\n3. Criando template simplificado...")
    create_simple_perfil_template()
    
    print("\n4. Reiniciando e testando...")
    restart_and_test()
    
    print("\n" + "="*60)
    print("🎯 PRÓXIMOS PASSOS:")
    print("="*60)
    print("1. Acesse: https://assessments.zerobox.com.br/auth/perfil-test")
    print("   (deve mostrar informações de debug)")
    print()
    print("2. Acesse: https://assessments.zerobox.com.br/auth/perfil") 
    print("   (deve funcionar ou mostrar erro detalhado)")
    print()
    print("3. Verifique logs em tempo real:")
    print("   tail -f /var/log/supervisor/assessment-*.log")
    print()
    print("📂 BACKUPS CRIADOS:")
    print("   /var/www/assessment/routes/auth.py.debug_backup")
    print("   /var/www/assessment/templates/auth/perfil.html.debug_backup")
    print()
    print("🔧 Para monitorar logs em tempo real:")
    print("   python3 diagnostico_perfil_admin.py --monitor")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
        monitor_logs_realtime()
    else:
        main()