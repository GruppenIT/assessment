#!/usr/bin/env python3
"""
Script de troubleshooting para diagnosticar erro na página de perfil on-premise
"""

import os
import sys
import traceback
import subprocess

def check_environment():
    """Verificar ambiente e dependências"""
    print("🔍 DIAGNÓSTICO DO AMBIENTE ON-PREMISE")
    print("="*50)
    
    # Verificar se está no diretório correto
    if not os.path.exists('/var/www/assessment'):
        print("❌ Diretório /var/www/assessment não encontrado")
        return False
    
    os.chdir('/var/www/assessment')
    print("✅ Diretório correto: /var/www/assessment")
    
    # Verificar arquivos essenciais
    essential_files = [
        'routes/auth.py',
        'templates/auth/perfil.html',
        'forms/auth_forms.py',
        'app.py'
    ]
    
    for file in essential_files:
        if os.path.exists(file):
            print(f"✅ {file} existe")
        else:
            print(f"❌ {file} não encontrado")
            return False
    
    return True

def check_python_syntax():
    """Verificar sintaxe Python dos arquivos críticos"""
    print("\n🐍 VERIFICANDO SINTAXE PYTHON")
    print("-"*30)
    
    files_to_check = [
        'routes/auth.py',
        'forms/auth_forms.py',
        'app.py'
    ]
    
    all_ok = True
    
    for file in files_to_check:
        try:
            with open(file, 'r') as f:
                code = f.read()
            
            compile(code, file, 'exec')
            print(f"✅ {file} - sintaxe OK")
            
        except SyntaxError as e:
            print(f"❌ {file} - erro de sintaxe:")
            print(f"   Linha {e.lineno}: {e.msg}")
            print(f"   Código: {e.text}")
            all_ok = False
        except Exception as e:
            print(f"❌ {file} - erro: {e}")
            all_ok = False
    
    return all_ok

def test_imports():
    """Testar imports críticos"""
    print("\n📦 TESTANDO IMPORTS")
    print("-"*20)
    
    # Adicionar diretório atual ao path
    sys.path.insert(0, '/var/www/assessment')
    
    # Definir variáveis de ambiente básicas
    os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')
    os.environ.setdefault('SECRET_KEY', 'test')
    
    try:
        # Testar imports básicos
        from flask import Flask, request
        print("✅ Flask imports OK")
        
        from werkzeug.security import check_password_hash, generate_password_hash
        print("✅ Werkzeug security OK")
        
        # Testar forms
        from forms.auth_forms import LoginForm
        print("✅ LoginForm import OK")
        
        # Verificar se AlterarSenhaForm ainda existe (não deveria)
        try:
            from forms.auth_forms import AlterarSenhaForm
            print("⚠️  AlterarSenhaForm ainda existe (deveria ter sido removido)")
        except ImportError:
            print("✅ AlterarSenhaForm corretamente removido")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro de import: {e}")
        traceback.print_exc()
        return False

def check_auth_route():
    """Verificar rota de auth especificamente"""
    print("\n🛣️  VERIFICANDO ROTA AUTH/PERFIL")
    print("-"*30)
    
    try:
        with open('routes/auth.py', 'r') as f:
            content = f.read()
        
        # Verificar se função perfil existe
        if 'def perfil(' not in content:
            print("❌ Função perfil() não encontrada")
            return False
        
        print("✅ Função perfil() encontrada")
        
        # Verificar se tem métodos GET e POST
        if "methods=['GET', 'POST']" in content:
            print("✅ Métodos GET/POST configurados")
        else:
            print("❌ Métodos GET/POST não configurados")
            return False
        
        # Verificar se não tem dependência de FlaskForm
        if 'AlterarSenhaForm()' in content:
            print("❌ Ainda tem dependência de AlterarSenhaForm")
            return False
        
        print("✅ Sem dependência de FlaskForm")
        
        # Verificar se tem validação manual
        if 'request.form.get(' in content:
            print("✅ Validação manual implementada")
        else:
            print("❌ Validação manual não encontrada")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar auth.py: {e}")
        return False

def check_template():
    """Verificar template de perfil"""
    print("\n🎨 VERIFICANDO TEMPLATE")
    print("-"*25)
    
    try:
        with open('templates/auth/perfil.html', 'r') as f:
            content = f.read()
        
        # Verificar se não tem referências ao form
        if '{{ form.' in content:
            print("❌ Template ainda tem referências a {{ form. }}")
            return False
        
        print("✅ Template sem referências a form")
        
        # Verificar se tem campos HTML manuais
        if 'name="senha_atual"' in content and 'name="nova_senha"' in content:
            print("✅ Campos HTML manuais encontrados")
        else:
            print("❌ Campos HTML manuais não encontrados")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar template: {e}")
        return False

def fix_auth_route():
    """Corrigir rota de auth se necessário"""
    print("\n🔧 APLICANDO CORREÇÃO NA ROTA AUTH")
    print("-"*35)
    
    try:
        with open('routes/auth.py', 'r') as f:
            content = f.read()
        
        # Backup
        with open('routes/auth.py.backup', 'w') as f:
            f.write(content)
        
        # Corrigir import se ainda tem AlterarSenhaForm
        if 'AlterarSenhaForm' in content:
            content = content.replace(
                'from forms.auth_forms import LoginForm, AlterarSenhaForm',
                'from forms.auth_forms import LoginForm'
            )
            print("✅ Import corrigido")
        
        # Substituir função perfil se ainda está com FlaskForm
        if 'AlterarSenhaForm()' in content:
            # Encontrar e substituir a função perfil inteira
            import re
            
            new_perfil = '''@auth_bp.route('/perfil', methods=['GET', 'POST'])
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
            
            # Substituir função perfil
            pattern = r'@auth_bp\.route\(\'/perfil\'.*?def perfil\(.*?\):.*?return render_template\([^)]+\)'
            content = re.sub(pattern, new_perfil, content, flags=re.DOTALL)
            print("✅ Função perfil corrigida")
        
        # Salvar arquivo corrigido
        with open('routes/auth.py', 'w') as f:
            f.write(content)
        
        print("✅ Arquivo routes/auth.py corrigido")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir auth.py: {e}")
        # Restaurar backup se deu erro
        try:
            with open('routes/auth.py.backup', 'r') as f:
                backup_content = f.read()
            with open('routes/auth.py', 'w') as f:
                f.write(backup_content)
            print("✅ Backup restaurado")
        except:
            pass
        return False

def fix_template():
    """Corrigir template se necessário"""
    print("\n🎨 CORRIGINDO TEMPLATE")
    print("-"*22)
    
    try:
        with open('templates/auth/perfil.html', 'r') as f:
            content = f.read()
        
        # Backup
        with open('templates/auth/perfil.html.backup', 'w') as f:
            f.write(content)
        
        if '{{ form.' in content:
            # Corrigir referências ao form
            content = content.replace('{{ form.hidden_tag() }}', '')
            
            # Substituir campos do form por HTML puro
            content = content.replace(
                '{{ form.senha_atual.label(class="form-label") }}',
                '<label for="senha_atual" class="form-label">Senha Atual</label>'
            )
            content = content.replace(
                '{{ form.senha_atual(class="form-control") }}',
                '<input type="password" class="form-control" id="senha_atual" name="senha_atual" placeholder="Digite sua senha atual" required>'
            )
            
            content = content.replace(
                '{{ form.nova_senha.label(class="form-label") }}',
                '<label for="nova_senha" class="form-label">Nova Senha</label>'
            )
            content = content.replace(
                '{{ form.nova_senha(class="form-control") }}',
                '<input type="password" class="form-control" id="nova_senha" name="nova_senha" placeholder="Digite a nova senha" minlength="6" required>'
            )
            
            content = content.replace(
                '{{ form.confirmar_nova_senha.label(class="form-label") }}',
                '<label for="confirmar_nova_senha" class="form-label">Confirmar Nova Senha</label>'
            )
            content = content.replace(
                '{{ form.confirmar_nova_senha(class="form-control") }}',
                '<input type="password" class="form-control" id="confirmar_nova_senha" name="confirmar_nova_senha" placeholder="Digite a nova senha novamente" minlength="6" required>'
            )
            
            content = content.replace(
                '{{ form.submit(class="btn btn-primary") }}',
                '<button type="submit" class="btn btn-primary"><i class="fas fa-key me-2"></i>Alterar Senha</button>'
            )
            
            # Remover loops de erro do form
            import re
            content = re.sub(r'\{% for error in form\.[^}]+\.errors %\}.*?\{% endfor %\}', '', content, flags=re.DOTALL)
            
            # Salvar template corrigido
            with open('templates/auth/perfil.html', 'w') as f:
                f.write(content)
            
            print("✅ Template corrigido")
            return True
        
        print("✅ Template já está correto")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir template: {e}")
        # Restaurar backup se deu erro
        try:
            with open('templates/auth/perfil.html.backup', 'r') as f:
                backup_content = f.read()
            with open('templates/auth/perfil.html', 'w') as f:
                f.write(backup_content)
            print("✅ Backup do template restaurado")
        except:
            pass
        return False

def restart_service():
    """Reiniciar serviço"""
    print("\n🔄 REINICIANDO SERVIÇO")
    print("-"*20)
    
    try:
        subprocess.run(['supervisorctl', 'restart', 'assessment'], check=True)
        print("✅ Serviço reiniciado")
        return True
    except Exception as e:
        print(f"❌ Erro ao reiniciar serviço: {e}")
        return False

def test_route():
    """Testar rota após correções"""
    print("\n🧪 TESTANDO ROTA")
    print("-"*15)
    
    try:
        import time
        time.sleep(3)  # Aguardar serviço inicializar
        
        import requests
        response = requests.get('http://localhost:8000/auth/perfil', timeout=10)
        
        if response.status_code == 200:
            print("✅ Rota /auth/perfil respondendo OK")
            return True
        elif response.status_code == 302:
            print("⚠️  Rota redirecionando (pode ser falta de login)")
            return True
        else:
            print(f"❌ Rota retornou código {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao testar rota: {e}")
        return False
    except ImportError:
        print("⚠️  Módulo requests não disponível para teste")
        return True

def main():
    """Função principal"""
    print("🩺 TROUBLESHOOTING - PERFIL ON-PREMISE")
    print("="*50)
    
    if not check_environment():
        print("\n❌ ERRO: Ambiente não está configurado corretamente")
        return False
    
    if not check_python_syntax():
        print("\n❌ ERRO: Problemas de sintaxe encontrados")
        return False
    
    if not test_imports():
        print("\n❌ ERRO: Problemas de import encontrados")
        return False
    
    if not check_auth_route():
        print("\n⚠️  PROBLEMA: Rota auth precisa de correção")
        if not fix_auth_route():
            print("\n❌ ERRO: Não foi possível corrigir rota auth")
            return False
    
    if not check_template():
        print("\n⚠️  PROBLEMA: Template precisa de correção")
        if not fix_template():
            print("\n❌ ERRO: Não foi possível corrigir template")
            return False
    
    if not restart_service():
        print("\n⚠️  AVISO: Não foi possível reiniciar serviço automaticamente")
        print("Execute manualmente: sudo supervisorctl restart assessment")
    
    test_route()
    
    print("\n✅ DIAGNÓSTICO CONCLUÍDO")
    print("="*30)
    print("Agora teste a rota: http://seu-servidor:8000/auth/perfil")
    
    return True

if __name__ == "__main__":
    main()