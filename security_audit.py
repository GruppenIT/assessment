#!/usr/bin/env python3
"""
Script de auditoria de segurança para identificar rotas desprotegidas
"""

import os
import re
import ast
from pathlib import Path

def find_route_definitions(file_path):
    """Encontra todas as definições de rotas em um arquivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Padrões para encontrar rotas
        route_patterns = [
            r'@\w+\.route\([\'"]([^\'\"]+)[\'"][^\)]*\)',  # @bp.route('/path')
            r'@app\.route\([\'"]([^\'\"]+)[\'"][^\)]*\)',   # @app.route('/path')
        ]
        
        routes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Procurar por decoradores de rota
            for pattern in route_patterns:
                match = re.search(pattern, line)
                if match:
                    route_path = match.group(1)
                    
                    # Procurar por decoradores de autenticação nas linhas seguintes
                    auth_decorators = []
                    function_name = None
                    
                    # Analisar linhas seguintes para encontrar decoradores e função
                    for j in range(i+1, min(i+10, len(lines))):
                        next_line = lines[j].strip()
                        
                        # Decoradores de autenticação
                        if '@login_required' in next_line:
                            auth_decorators.append('login_required')
                        elif '@admin_required' in next_line:
                            auth_decorators.append('admin_required')
                        elif '@respondente_required' in next_line:
                            auth_decorators.append('respondente_required')
                        elif '@cliente_required' in next_line:
                            auth_decorators.append('cliente_required')
                        elif '@admin_or_owner_required' in next_line:
                            auth_decorators.append('admin_or_owner_required')
                        
                        # Encontrar nome da função
                        func_match = re.match(r'def (\w+)\(', next_line)
                        if func_match:
                            function_name = func_match.group(1)
                            break
                    
                    routes.append({
                        'path': route_path,
                        'function': function_name,
                        'file': file_path,
                        'line': i + 1,
                        'auth_decorators': auth_decorators,
                        'protected': len(auth_decorators) > 0
                    })
        
        return routes
    except Exception as e:
        print(f"Erro ao analisar {file_path}: {e}")
        return []

def audit_security():
    """Executa auditoria completa de segurança das rotas"""
    
    print("🔍 AUDITORIA DE SEGURANÇA DAS ROTAS")
    print("="*60)
    
    # Diretórios para analisar
    directories = ['routes/', 'app.py']
    
    all_routes = []
    
    # Analisar todos os arquivos Python nos diretórios
    for directory in directories:
        if os.path.isfile(directory):
            # Arquivo único
            routes = find_route_definitions(directory)
            all_routes.extend(routes)
        elif os.path.isdir(directory):
            # Diretório
            for file_path in Path(directory).rglob('*.py'):
                if '__pycache__' not in str(file_path):
                    routes = find_route_definitions(str(file_path))
                    all_routes.extend(routes)
    
    # Separar rotas por categoria
    rotas_publicas = []
    rotas_protegidas = []
    rotas_desprotegidas = []
    rotas_suspeitas = []
    
    for route in all_routes:
        path = route['path']
        function = route['function']
        
        # Rotas que devem ser públicas
        if (path in ['/login', '/logout'] or 
            path.startswith('/static') or 
            path == '/favicon.ico'):
            rotas_publicas.append(route)
        
        # Rotas com proteção
        elif route['protected']:
            rotas_protegidas.append(route)
        
        # Rotas suspeitas (auto-login, test, etc.)
        elif (function and ('auto_login' in function.lower() or 
                          'test' in function.lower() or
                          'debug' in function.lower())):
            rotas_suspeitas.append(route)
        
        # Rotas desprotegidas
        else:
            rotas_desprotegidas.append(route)
    
    # Exibir relatório
    print(f"\n📊 RESUMO DA AUDITORIA:")
    print(f"   Total de rotas encontradas: {len(all_routes)}")
    print(f"   Rotas públicas (OK): {len(rotas_publicas)}")
    print(f"   Rotas protegidas (OK): {len(rotas_protegidas)}")
    print(f"   ⚠️  Rotas desprotegidas: {len(rotas_desprotegidas)}")
    print(f"   🚨 Rotas suspeitas: {len(rotas_suspeitas)}")
    
    if rotas_desprotegidas:
        print(f"\n❌ ROTAS DESPROTEGIDAS (VULNERABILIDADE):")
        print("-"*50)
        for route in rotas_desprotegidas:
            print(f"   {route['path']} -> {route['function']}()")
            print(f"      📄 {route['file']}:{route['line']}")
    
    if rotas_suspeitas:
        print(f"\n🚨 ROTAS SUSPEITAS (RISCO DE SEGURANÇA):")
        print("-"*50)
        for route in rotas_suspeitas:
            print(f"   {route['path']} -> {route['function']}()")
            print(f"      📄 {route['file']}:{route['line']}")
            print(f"      ⚠️  Tipo: Rota de teste/debug")
    
    if rotas_protegidas:
        print(f"\n✅ ROTAS PROTEGIDAS (SEGURAS):")
        print("-"*50)
        for route in rotas_protegidas[:10]:  # Mostrar apenas primeiras 10
            decorators = ', '.join(route['auth_decorators'])
            print(f"   {route['path']} -> {route['function']}() [{decorators}]")
        
        if len(rotas_protegidas) > 10:
            print(f"   ... e mais {len(rotas_protegidas) - 10} rotas protegidas")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES DE SEGURANÇA:")
    print("-"*50)
    
    if rotas_desprotegidas:
        print("   1. Adicionar @login_required em todas as rotas desprotegidas")
        print("   2. Adicionar decoradores específicos (@admin_required, etc.)")
    
    if rotas_suspeitas:
        print("   3. REMOVER rotas de auto-login em produção")
        print("   4. REMOVER rotas de teste e debug em produção")
    
    print("   5. Implementar middleware global de autenticação")
    print("   6. Configurar HTTPS obrigatório")
    print("   7. Implementar rate limiting")
    print("   8. Logs de auditoria para acessos não autorizados")
    
    return {
        'total': len(all_routes),
        'publicas': len(rotas_publicas),
        'protegidas': len(rotas_protegidas),
        'desprotegidas': len(rotas_desprotegidas),
        'suspeitas': len(rotas_suspeitas),
        'vulnerabilidades': rotas_desprotegidas + rotas_suspeitas
    }

if __name__ == "__main__":
    audit_security()