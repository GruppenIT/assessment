#!/usr/bin/env python3
"""
Script para aplicar manualmente o patch de segurança no app.py on-premise
"""

import re
import sys
import os

def patch_app_py():
    """Aplica o middleware de segurança no app.py"""
    
    app_py_path = "/var/www/assessment/app.py"
    
    if not os.path.exists(app_py_path):
        print("❌ Arquivo app.py não encontrado em /var/www/assessment/")
        return False
    
    # Middleware code to inject
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
    
    try:
        # Read current file
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if middleware already exists
        if '@app.before_request' in content and 'require_login' in content:
            print("ℹ️  Middleware de segurança já existe no app.py")
            return True
        
        # Find location to insert middleware (after blueprints registration)
        pattern = r'(app\.register_blueprint\([^)]+\)[^\n]*\n)'
        matches = list(re.finditer(pattern, content))
        
        if not matches:
            print("❌ Não foi possível encontrar local para inserir middleware")
            return False
        
        # Insert after the last blueprint registration
        last_match = matches[-1]
        insert_pos = last_match.end()
        
        new_content = content[:insert_pos] + middleware_code + content[insert_pos:]
        
        # Backup original
        backup_path = app_py_path + '.backup_' + str(int(__import__('time').time()))
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup criado: {backup_path}")
        
        # Write patched version
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Middleware de segurança adicionado ao app.py")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar patch: {e}")
        return False

def remove_auto_login_routes():
    """Remove rotas de auto-login dos arquivos de rotas"""
    
    files_to_patch = [
        '/var/www/assessment/routes/auth.py',
        '/var/www/assessment/routes/respondente.py',
        '/var/www/assessment/routes/projeto.py'
    ]
    
    for file_path in files_to_patch:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            skip_until_next_route = False
            
            for line in lines:
                # Se encontrou uma rota de auto-login, pular até a próxima rota
                if '@' in line and 'route' in line and 'auto' in line and 'login' in line:
                    skip_until_next_route = True
                    continue
                
                # Se está pulando e encontrou uma nova rota
                if skip_until_next_route:
                    if line.startswith('@') or (line.strip().startswith('def ') and 'auto_login' not in line):
                        skip_until_next_route = False
                        new_lines.append(line)
                    continue
                
                # Pular linhas de função auto_login
                if line.strip().startswith('def auto_login'):
                    skip_until_next_route = True
                    continue
                
                new_lines.append(line)
            
            # Escrever arquivo modificado
            if len(new_lines) != len(lines):
                backup_path = file_path + '.backup_' + str(int(__import__('time').time()))
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print(f"✅ Rotas de auto-login removidas de {file_path}")
            
        except Exception as e:
            print(f"❌ Erro ao processar {file_path}: {e}")

def main():
    """Função principal"""
    
    print("🔐 APLICANDO PATCH DE SEGURANÇA MANUAL")
    print("="*50)
    
    # Verificar se está executando como root
    if os.geteuid() != 0:
        print("❌ Este script deve ser executado como root (sudo)")
        sys.exit(1)
    
    # 1. Aplicar middleware no app.py
    print("1. Aplicando middleware de segurança...")
    if not patch_app_py():
        print("❌ Falha ao aplicar patch no app.py")
        sys.exit(1)
    
    # 2. Remover rotas de auto-login
    print("2. Removendo rotas de auto-login...")
    remove_auto_login_routes()
    
    print("\n✅ PATCH APLICADO COM SUCESSO!")
    print("Agora execute:")
    print("  sudo supervisorctl restart assessment")
    print("  curl -I http://localhost:8000/admin/projetos/working")

if __name__ == "__main__":
    main()