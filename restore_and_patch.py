#!/usr/bin/env python3
"""
Script seguro para restaurar backup e aplicar patch correto
"""

import os
import sys
import re

def restore_backup():
    """Restaura o backup original do app.py"""
    
    backup_file = "/var/www/assessment/app.py.backup_1756498913"
    app_file = "/var/www/assessment/app.py"
    
    if not os.path.exists(backup_file):
        print("❌ Backup não encontrado:", backup_file)
        return False
    
    try:
        import shutil
        shutil.copy2(backup_file, app_file)
        print("✅ Backup restaurado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao restaurar backup: {e}")
        return False

def apply_safe_patch():
    """Aplica patch seguro no app.py"""
    
    app_file = "/var/www/assessment/app.py"
    
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
        # Ler arquivo atual
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se middleware já existe
        if '@app.before_request' in content and 'require_login' in content:
            print("ℹ️  Middleware já existe no arquivo")
            return True
        
        # Procurar pelo final da função create_app (antes do return app)
        pattern = r'(\s+return app\s*\n)'
        match = re.search(pattern, content)
        
        if not match:
            print("❌ Não foi possível encontrar 'return app' no arquivo")
            return False
        
        # Inserir middleware antes do return app
        insert_pos = match.start()
        new_content = content[:insert_pos] + middleware_code + content[insert_pos:]
        
        # Fazer backup antes de modificar
        backup_path = app_file + '.safe_backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Escrever conteúdo modificado
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Middleware adicionado com segurança")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar patch: {e}")
        return False

def test_syntax():
    """Testa a sintaxe do arquivo Python"""
    
    try:
        import py_compile
        py_compile.compile('/var/www/assessment/app.py', doraise=True)
        print("✅ Sintaxe verificada - OK")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Erro de sintaxe: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar sintaxe: {e}")
        return False

def main():
    """Função principal"""
    
    print("🔧 CORREÇÃO SEGURA DE SINTAXE")
    print("="*40)
    
    if os.geteuid() != 0:
        print("❌ Execute como root (sudo)")
        sys.exit(1)
    
    # 1. Restaurar backup
    print("1. Restaurando backup original...")
    if not restore_backup():
        sys.exit(1)
    
    # 2. Aplicar patch seguro
    print("2. Aplicando patch seguro...")
    if not apply_safe_patch():
        sys.exit(1)
    
    # 3. Testar sintaxe
    print("3. Verificando sintaxe...")
    if not test_syntax():
        print("🔄 Restaurando backup devido a erro de sintaxe...")
        restore_backup()
        sys.exit(1)
    
    print("\n✅ PATCH APLICADO COM SUCESSO!")
    print("Execute agora:")
    print("  sudo supervisorctl restart assessment")
    print("  curl -I http://localhost:8000/admin/projetos/working")

if __name__ == "__main__":
    main()