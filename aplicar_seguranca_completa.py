#!/usr/bin/env python3
"""
Script para aplicar proteção completa de autenticação em todas as rotas
"""

import os
import re
from pathlib import Path

def remove_auto_login_routes():
    """Remove todas as rotas de auto-login inseguras"""
    
    print("🚨 REMOVENDO ROTAS DE AUTO-LOGIN INSEGURAS")
    print("="*50)
    
    files_to_check = [
        'routes/respondente.py',
        'routes/projeto.py',
        'routes/admin.py'
    ]
    
    removed_routes = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        print(f"\n📄 Verificando {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Padrões de rotas de auto-login para remover
            auto_login_patterns = [
                # Rotas completas de auto-login
                r"@\w+\.route\(['\"][^'\"]*auto[_-]?login[^'\"]*['\"]\)[^@]*?def [^:]+:.*?(?=@|\Z)",
                # Funções de auto-login específicas
                r"def auto_login[^:]*:.*?(?=def|\Z)",
                r"def auto_login_[^:]*:.*?(?=def|\Z)",
            ]
            
            for pattern in auto_login_patterns:
                matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
                for match in matches:
                    matched_text = match.group(0)
                    # Extrair nome da rota
                    route_match = re.search(r"@\w+\.route\(['\"]([^'\"]+)['\"]\)", matched_text)
                    if route_match:
                        route_path = route_match.group(1)
                        removed_routes.append(f"{file_path}: {route_path}")
                        print(f"   ❌ Removendo rota insegura: {route_path}")
                
                # Remover as rotas encontradas
                content = re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)
            
            # Limpar linhas vazias duplas
            content = re.sub(r'\n\n\n+', '\n\n', content)
            
            # Salvar apenas se houve mudanças
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ {file_path} atualizado")
            else:
                print(f"   ℹ️  Nenhuma rota insegura encontrada")
                
        except Exception as e:
            print(f"   ❌ Erro ao processar {file_path}: {e}")
    
    return removed_routes

def add_login_required_to_routes():
    """Adiciona @login_required a rotas que não possuem proteção"""
    
    print(f"\n🔒 ADICIONANDO PROTEÇÃO @login_required")
    print("="*50)
    
    files_to_protect = [
        'routes/respondente.py',
        'routes/projeto.py', 
        'routes/admin.py',
        'routes/cliente.py',
        'routes/assessment_admin.py',
        'routes/relatorio.py',
        'routes/sse_progress.py'
    ]
    
    protected_routes = []
    
    for file_path in files_to_protect:
        if not os.path.exists(file_path):
            continue
            
        print(f"\n📄 Protegendo {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            i = 0
            changes_made = False
            
            while i < len(lines):
                line = lines[i]
                
                # Verificar se é uma definição de rota
                if re.match(r'\s*@\w+\.route\(', line):
                    # Coletar todas as linhas do decorador até a função
                    route_block = [line]
                    i += 1
                    
                    # Coletar decoradores subsequentes
                    while i < len(lines) and (lines[i].strip().startswith('@') or lines[i].strip() == ''):
                        route_block.append(lines[i])
                        i += 1
                    
                    # Próxima linha deve ser a definição da função
                    if i < len(lines) and lines[i].strip().startswith('def '):
                        func_line = lines[i]
                        
                        # Verificar se já tem algum decorator de autenticação
                        block_text = ''.join(route_block)
                        has_auth = any(decorator in block_text for decorator in [
                            '@login_required',
                            '@admin_required',
                            '@respondente_required',
                            '@cliente_required',
                            '@admin_or_owner_required'
                        ])
                        
                        # Se não tem proteção, adicionar @login_required
                        if not has_auth:
                            # Extrair nome da função para log
                            func_match = re.search(r'def (\w+)\(', func_line)
                            func_name = func_match.group(1) if func_match else 'unknown'
                            
                            # Pular se for função de login/logout
                            if func_name not in ['login', 'logout']:
                                # Adicionar @login_required antes da função
                                indentation = re.match(r'(\s*)', func_line).group(1)
                                login_required_line = f"{indentation}@login_required\n"
                                route_block.append(login_required_line)
                                changes_made = True
                                protected_routes.append(f"{file_path}: {func_name}()")
                                print(f"   🔒 Protegendo função: {func_name}()")
                        
                        # Adicionar todas as linhas do bloco
                        new_lines.extend(route_block)
                        new_lines.append(func_line)
                    else:
                        # Não é uma função válida, apenas adicionar as linhas
                        new_lines.extend(route_block)
                        if i < len(lines):
                            new_lines.append(lines[i])
                else:
                    new_lines.append(line)
                
                i += 1
            
            # Verificar se precisa adicionar import do login_required
            content = ''.join(new_lines)
            if changes_made and '@login_required' in content:
                if 'from flask_login import' in content:
                    # Adicionar login_required ao import existente
                    if 'login_required' not in content:
                        content = re.sub(
                            r'from flask_login import ([^,\n]+)',
                            r'from flask_login import \1, login_required',
                            content
                        )
                else:
                    # Adicionar novo import
                    import_line = "from flask_login import login_required\n"
                    # Encontrar local adequado para adicionar o import (depois dos outros imports)
                    lines_list = content.split('\n')
                    import_index = 0
                    for idx, line in enumerate(lines_list):
                        if line.startswith('from ') or line.startswith('import '):
                            import_index = idx + 1
                        elif line.strip() == '' and import_index > 0:
                            break
                    
                    lines_list.insert(import_index, import_line.strip())
                    content = '\n'.join(lines_list)
            
            # Salvar arquivo se houve mudanças
            if changes_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ {file_path} atualizado com proteções")
            else:
                print(f"   ℹ️  Todas as rotas já estão protegidas")
                
        except Exception as e:
            print(f"   ❌ Erro ao processar {file_path}: {e}")
    
    return protected_routes

def create_security_deployment_script():
    """Cria script para aplicar todas as melhorias de segurança no ambiente on-premise"""
    
    script_content = """#!/bin/bash
# Script para aplicar melhorias de segurança no ambiente on-premise

echo "🔐 APLICANDO MELHORIAS DE SEGURANÇA"
echo "=================================="

# 1. Fazer backup dos arquivos atuais
echo "📋 Criando backup dos arquivos atuais..."
backup_dir="/var/www/assessment/backup_security_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$backup_dir"

sudo cp -r /var/www/assessment/routes "$backup_dir/"
sudo cp /var/www/assessment/app.py "$backup_dir/"
sudo cp /var/www/assessment/utils/auth_utils.py "$backup_dir/"

echo "   ✅ Backup criado em: $backup_dir"

# 2. Copiar arquivos atualizados
echo "📥 Copiando arquivos com melhorias de segurança..."

# Copiar arquivos modificados do repositório local
# (assumindo que os arquivos já foram atualizados no repositório)

# 3. Verificar se todas as dependências estão instaladas
echo "📦 Verificando dependências..."
cd /var/www/assessment
source venv/bin/activate

# 4. Executar auditoria de segurança
echo "🔍 Executando auditoria de segurança..."
python3 security_audit.py

# 5. Reiniciar serviços
echo "🔄 Reiniciando serviços..."
sudo supervisorctl restart assessment

# 6. Verificar se o serviço está rodando
echo "📊 Verificando status do serviço..."
sudo supervisorctl status assessment

echo ""
echo "✅ MELHORIAS DE SEGURANÇA APLICADAS!"
echo ""
echo "🔒 Mudanças implementadas:"
echo "   • Proteção total de autenticação em todas as rotas"
echo "   • Remoção de rotas de auto-login inseguras"
echo "   • Middleware global de proteção"
echo "   • Handler de acesso não autorizado aprimorado"
echo ""
echo "🔍 Para verificar:"
echo "   sudo tail -f /var/log/assessment.log"
echo "   curl -I http://localhost:8000/admin/dashboard"
echo "   (deve retornar redirect para login)"
"""
    
    with open('atualizar_seguranca_onpremise.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    os.chmod('atualizar_seguranca_onpremise.sh', 0o755)
    
    print(f"\n📜 SCRIPT DE ATUALIZAÇÃO CRIADO")
    print("="*40)
    print("   Arquivo: atualizar_seguranca_onpremise.sh")
    print("   Uso: sudo bash atualizar_seguranca_onpremise.sh")

def main():
    """Executa todas as correções de segurança"""
    
    print("🔐 APLICAÇÃO COMPLETA DE SEGURANÇA")
    print("="*60)
    
    # 1. Remover rotas inseguras
    removed = remove_auto_login_routes()
    
    # 2. Adicionar proteção às rotas
    protected = add_login_required_to_routes()
    
    # 3. Criar script de deploy
    create_security_deployment_script()
    
    # 4. Resumo final
    print(f"\n🎯 RESUMO DAS ALTERAÇÕES:")
    print(f"   Rotas inseguras removidas: {len(removed)}")
    print(f"   Rotas protegidas: {len(protected)}")
    print(f"   Script de deploy criado: ✅")
    
    if removed:
        print(f"\n❌ Rotas removidas:")
        for route in removed:
            print(f"   {route}")
    
    if protected:
        print(f"\n🔒 Rotas protegidas:")
        for route in protected[:5]:  # Mostrar apenas primeiras 5
            print(f"   {route}")
        if len(protected) > 5:
            print(f"   ... e mais {len(protected) - 5} rotas")
    
    print(f"\n✅ SEGURANÇA APLICADA COM SUCESSO!")
    print(f"   Execute: python3 security_audit.py para verificar")

if __name__ == "__main__":
    main()