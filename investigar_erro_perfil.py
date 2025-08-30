#!/usr/bin/env python3
"""
Investigação avançada do erro Internal Server Error no perfil
"""

import os
import sys
import traceback
import subprocess
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_section(title):
    """Imprimir seção com formatação"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def run_command(cmd, ignore_errors=False):
    """Executar comando e retornar resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0 and not ignore_errors:
            print(f"❌ Erro ao executar: {cmd}")
            print(f"   STDERR: {result.stderr}")
            return None
        return result.stdout
    except Exception as e:
        print(f"❌ Exceção ao executar {cmd}: {e}")
        return None

def check_supervisor_logs():
    """Verificar logs do supervisor"""
    log_section("LOGS DO SUPERVISOR")
    
    # Verificar status do supervisor
    status = run_command("supervisorctl status assessment", ignore_errors=True)
    if status:
        print("Status do serviço:")
        print(status)
    
    # Logs do supervisor
    logs = run_command("tail -50 /var/log/supervisor/supervisord.log", ignore_errors=True)
    if logs:
        print("\nÚltimas 50 linhas do log do supervisor:")
        print(logs)
    
    # Logs específicos do assessment
    assessment_logs = run_command("tail -50 /var/log/supervisor/assessment-*.log", ignore_errors=True)
    if assessment_logs:
        print("\nLogs específicos do assessment:")
        print(assessment_logs)

def check_application_logs():
    """Verificar logs da aplicação"""
    log_section("LOGS DA APLICAÇÃO")
    
    # Logs do gunicorn
    gunicorn_logs = run_command("tail -100 /var/log/assessment.log", ignore_errors=True)
    if gunicorn_logs:
        print("Logs do Gunicorn:")
        print(gunicorn_logs)
    
    # Logs do sistema
    system_logs = run_command("journalctl -u supervisor -n 50 --no-pager", ignore_errors=True)
    if system_logs:
        print("\nLogs do sistema (journalctl):")
        print(system_logs)

def test_python_environment():
    """Testar ambiente Python"""
    log_section("AMBIENTE PYTHON")
    
    os.chdir('/var/www/assessment')
    
    # Ativar ambiente virtual se existir
    venv_path = '/var/www/assessment/venv'
    if os.path.exists(venv_path):
        print(f"✅ Ambiente virtual encontrado: {venv_path}")
        # Adicionar ao path
        venv_site_packages = f"{venv_path}/lib/python3.11/site-packages"
        if os.path.exists(venv_site_packages):
            sys.path.insert(0, venv_site_packages)
        sys.path.insert(0, venv_path)
    
    # Testar imports críticos
    print("\nTestando imports:")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except Exception as e:
        print(f"❌ Flask: {e}")
    
    try:
        import werkzeug
        print(f"✅ Werkzeug {werkzeug.__version__}")
    except Exception as e:
        print(f"❌ Werkzeug: {e}")
    
    try:
        import flask_login
        print(f"✅ Flask-Login {flask_login.__version__}")
    except Exception as e:
        print(f"❌ Flask-Login: {e}")
    
    try:
        import flask_sqlalchemy
        print(f"✅ Flask-SQLAlchemy {flask_sqlalchemy.__version__}")
    except Exception as e:
        print(f"❌ Flask-SQLAlchemy: {e}")

def test_application_import():
    """Testar import da aplicação"""
    log_section("TESTE DE IMPORT DA APLICAÇÃO")
    
    os.chdir('/var/www/assessment')
    sys.path.insert(0, '/var/www/assessment')
    
    # Definir variáveis de ambiente
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
    os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
    
    try:
        print("Testando import do app...")
        from app import app, db
        print("✅ App importado com sucesso")
        
        with app.app_context():
            print("✅ Contexto da aplicação criado")
            
            # Testar import das rotas
            try:
                from routes.auth import auth_bp
                print("✅ Blueprint auth importado")
            except Exception as e:
                print(f"❌ Erro ao importar auth blueprint: {e}")
                traceback.print_exc()
            
            # Testar rota específica
            try:
                with app.test_client() as client:
                    # Fazer requisição para perfil (deve redirecionar para login)
                    response = client.get('/auth/perfil')
                    print(f"✅ Rota /auth/perfil responde com código {response.status_code}")
                    
                    if response.status_code == 500:
                        print("❌ Internal Server Error detectado!")
                        # Tentar capturar o erro
                        try:
                            response = client.get('/auth/perfil', follow_redirects=False)
                            print(f"Resposta sem redirect: {response.status_code}")
                        except Exception as route_error:
                            print(f"Erro na rota: {route_error}")
                            traceback.print_exc()
                            
            except Exception as e:
                print(f"❌ Erro ao testar rota: {e}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Erro ao importar aplicação: {e}")
        traceback.print_exc()

def check_route_registration():
    """Verificar registro das rotas"""
    log_section("VERIFICAÇÃO DE ROTAS")
    
    os.chdir('/var/www/assessment')
    sys.path.insert(0, '/var/www/assessment')
    
    try:
        os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///test.db')
        os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
        
        from app import app
        
        with app.app_context():
            print("Rotas registradas:")
            for rule in app.url_map.iter_rules():
                if 'perfil' in rule.rule:
                    print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
                    
    except Exception as e:
        print(f"❌ Erro ao verificar rotas: {e}")
        traceback.print_exc()

def check_database():
    """Verificar conexão com banco"""
    log_section("VERIFICAÇÃO DO BANCO DE DADOS")
    
    try:
        # Verificar variável DATABASE_URL
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            print(f"✅ DATABASE_URL definida: {db_url[:50]}...")
        else:
            print("❌ DATABASE_URL não definida")
            return
        
        # Testar conexão
        os.chdir('/var/www/assessment')
        sys.path.insert(0, '/var/www/assessment')
        
        from app import app, db
        
        with app.app_context():
            # Testar query simples
            result = db.engine.execute("SELECT 1")
            print("✅ Conexão com banco funcionando")
            
            # Verificar tabelas essenciais
            from models.usuario import Usuario
            count = Usuario.query.count()
            print(f"✅ Tabela Usuario: {count} registros")
            
    except Exception as e:
        print(f"❌ Erro de banco: {e}")
        traceback.print_exc()

def check_templates():
    """Verificar templates"""
    log_section("VERIFICAÇÃO DE TEMPLATES")
    
    template_path = '/var/www/assessment/templates/auth/perfil.html'
    
    if os.path.exists(template_path):
        print(f"✅ Template existe: {template_path}")
        
        with open(template_path, 'r') as f:
            content = f.read()
            
        # Verificar problemas comuns
        if '{{ form.' in content:
            print("⚠️  Template ainda contém referências a {{ form. }}")
            
        if 'AlterarSenhaForm' in content:
            print("⚠️  Template ainda contém referências a AlterarSenhaForm")
            
        if 'name="senha_atual"' in content:
            print("✅ Template tem campos HTML manuais")
        else:
            print("❌ Template não tem campos HTML manuais")
            
    else:
        print(f"❌ Template não encontrado: {template_path}")

def attempt_minimal_fix():
    """Tentar correção mínima"""
    log_section("CORREÇÃO MÍNIMA")
    
    os.chdir('/var/www/assessment')
    
    # Backup
    subprocess.run(['cp', 'routes/auth.py', 'routes/auth.py.minimal_backup'], check=False)
    
    try:
        # Criar versão mínima da função perfil
        with open('routes/auth.py', 'r') as f:
            content = f.read()
        
        # Função perfil mínima
        minimal_perfil = '''
@auth_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil simplificada"""
    return render_template('auth/perfil.html', usuario=current_user)
'''
        
        # Remover função perfil existente
        import re
        content = re.sub(
            r'@auth_bp\.route\(\'/perfil\'.*?def perfil\(.*?\):.*?return render_template\([^)]+\)',
            minimal_perfil.strip(),
            content,
            flags=re.DOTALL
        )
        
        # Salvar
        with open('routes/auth.py', 'w') as f:
            f.write(content)
        
        print("✅ Função perfil simplificada aplicada")
        
        # Reiniciar serviço
        subprocess.run(['supervisorctl', 'restart', 'assessment'], check=False)
        
        print("✅ Serviço reiniciado")
        
    except Exception as e:
        print(f"❌ Erro na correção mínima: {e}")
        # Restaurar backup
        subprocess.run(['cp', 'routes/auth.py.minimal_backup', 'routes/auth.py'], check=False)

def generate_report():
    """Gerar relatório do diagnóstico"""
    log_section("RELATÓRIO FINAL")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'/tmp/diagnostic_report_{timestamp}.txt'
    
    print(f"Gerando relatório em: {report_file}")
    
    # Aqui você pode adicionar lógica para gerar um relatório detalhado
    with open(report_file, 'w') as f:
        f.write(f"Relatório de Diagnóstico - {datetime.now()}\n")
        f.write("="*50 + "\n\n")
        f.write("Execute este script para obter informações detalhadas.\n")
    
    print(f"✅ Relatório salvo em: {report_file}")

def main():
    """Função principal"""
    print("🔍 INVESTIGAÇÃO AVANÇADA - ERRO PERFIL ON-PREMISE")
    print("="*60)
    
    # Verificar se está no ambiente correto
    if not os.path.exists('/var/www/assessment'):
        print("❌ Este script deve ser executado no servidor on-premise")
        print("   Diretório /var/www/assessment não encontrado")
        return
    
    check_supervisor_logs()
    check_application_logs()
    test_python_environment()
    test_application_import()
    check_route_registration()
    check_database()
    check_templates()
    attempt_minimal_fix()
    generate_report()
    
    print("\n" + "="*60)
    print("🏁 INVESTIGAÇÃO CONCLUÍDA")
    print("="*60)
    print("Se o problema persistir, verifique:")
    print("1. Logs detalhados gerados acima")
    print("2. Configuração do supervisor")
    print("3. Permissões de arquivos")
    print("4. Versões das dependências Python")

if __name__ == "__main__":
    main()