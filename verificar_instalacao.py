#!/usr/bin/env python3
"""
Script para verificar se a instalação do sistema está funcionando corretamente
Testa conectividade, banco de dados, permissões e funcionalidades principais
"""

import os
import sys
import psycopg2
import subprocess
from datetime import datetime
from urllib.parse import urlparse

# Carregar variáveis de ambiente
import env_loader

def verificar_sistema_operacional():
    """Verificar sistema operacional e dependências"""
    
    print("🖥️ Verificando sistema operacional...")
    
    try:
        # Verificar Ubuntu
        with open('/etc/os-release', 'r') as f:
            os_info = f.read()
            if 'Ubuntu' not in os_info:
                print("⚠️ Sistema não é Ubuntu (pode funcionar mas não testado)")
            else:
                print("✅ Ubuntu detectado")
        
        # Verificar serviços essenciais
        servicos = ['postgresql', 'nginx', 'supervisor']
        for servico in servicos:
            try:
                result = subprocess.run(['systemctl', 'is-active', servico], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {servico}: ativo")
                else:
                    print(f"⚠️ {servico}: inativo ou não instalado")
            except:
                print(f"❌ Não foi possível verificar {servico}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar sistema: {e}")
        return False

def verificar_variaveis_ambiente():
    """Verificar se as variáveis de ambiente estão configuradas"""
    
    print("🔧 Verificando variáveis de ambiente...")
    
    variaveis_obrigatorias = [
        'DATABASE_URL',
        'SESSION_SECRET', 
        'FLASK_SECRET_KEY'
    ]
    
    variaveis_opcionais = [
        'FLASK_ENV',
        'TZ',
        'TIMEZONE',
        'OPENAI_API_KEY'
    ]
    
    sucesso = True
    
    for var in variaveis_obrigatorias:
        valor = os.environ.get(var)
        if valor:
            if 'SECRET' in var or 'PASSWORD' in var:
                print(f"✅ {var}: configurada")
            elif 'DATABASE_URL' in var:
                if valor.startswith('postgresql'):
                    print(f"✅ {var}: PostgreSQL configurado")
                else:
                    print(f"❌ {var}: deve ser PostgreSQL")
                    sucesso = False
            else:
                print(f"✅ {var}: {valor}")
        else:
            print(f"❌ {var}: não configurada")
            sucesso = False
    
    for var in variaveis_opcionais:
        valor = os.environ.get(var)
        if valor:
            if 'SECRET' in var or 'KEY' in var:
                print(f"✅ {var}: configurada")
            else:
                print(f"✅ {var}: {valor}")
        else:
            print(f"⚠️ {var}: não configurada (opcional)")
    
    return sucesso

def verificar_banco_dados():
    """Verificar conectividade e estrutura do banco"""
    
    print("🗄️ Verificando banco de dados...")
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL não configurada")
            return False
            
        parsed = urlparse(database_url)
        
        # Testar conexão
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password
        )
        cursor = conn.cursor()
        
        # Verificar versão
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL conectado: {version[:50]}...")
        
        # Verificar tabelas principais
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tabelas = [row[0] for row in cursor.fetchall()]
        
        tabelas_esperadas = [
            'usuarios', 'clientes', 'respondentes', 'projetos',
            'assessment_tipos', 'assessment_versoes', 'assessment_dominios',
            'perguntas', 'respostas', 'auditoria', 'configuracoes'
        ]
        
        tabelas_encontradas = 0
        for tabela in tabelas_esperadas:
            if tabela in tabelas:
                tabelas_encontradas += 1
        
        print(f"✅ Tabelas encontradas: {tabelas_encontradas}/{len(tabelas_esperadas)}")
        
        if tabelas_encontradas < len(tabelas_esperadas) * 0.8:  # Pelo menos 80%
            print("⚠️ Algumas tabelas principais podem estar faltando")
            print(f"   Tabelas no banco: {', '.join(tabelas)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro no banco de dados: {e}")
        return False

def verificar_aplicacao_flask():
    """Verificar se a aplicação Flask carrega corretamente"""
    
    print("🌐 Verificando aplicação Flask...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Verificar configuração
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
            print(f"✅ Flask configurado com: {db_uri[:30]}...")
            
            # Testar query simples
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            if result[0] == 1:
                print("✅ Flask conectado ao banco com sucesso")
            
            # Verificar modelos
            from models.usuario import Usuario
            from models.configuracao import Configuracao
            
            admin_count = Usuario.query.count()
            config_count = Configuracao.query.count()
            
            print(f"✅ Usuários no sistema: {admin_count}")
            print(f"✅ Configurações no sistema: {config_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na aplicação Flask: {e}")
        return False

def verificar_permissoes_arquivos():
    """Verificar permissões de arquivos e diretórios"""
    
    print("📁 Verificando permissões de arquivos...")
    
    try:
        diretorio_app = '/var/www/assessment'
        
        if not os.path.exists(diretorio_app):
            print(f"❌ Diretório não encontrado: {diretorio_app}")
            return False
        
        # Verificar se é executável pelo usuário atual
        if os.access(diretorio_app, os.R_OK):
            print("✅ Diretório legível")
        else:
            print("❌ Diretório não legível")
            return False
        
        # Verificar arquivos principais
        arquivos_principais = [
            'main.py', 'app.py', 'env_loader.py',
            '.env', 'requirements.txt'
        ]
        
        for arquivo in arquivos_principais:
            caminho = os.path.join(diretorio_app, arquivo)
            if os.path.exists(caminho):
                if os.access(caminho, os.R_OK):
                    print(f"✅ {arquivo}: legível")
                else:
                    print(f"⚠️ {arquivo}: sem permissão de leitura")
            else:
                if arquivo == '.env':
                    print(f"⚠️ {arquivo}: não encontrado (verifique localização)")
                else:
                    print(f"❌ {arquivo}: não encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")
        return False

def verificar_supervisor():
    """Verificar se o supervisor está configurado"""
    
    print("👁️ Verificando supervisor...")
    
    try:
        # Verificar arquivo de configuração
        config_path = '/etc/supervisor/conf.d/assessment.conf'
        if os.path.exists(config_path):
            print("✅ Arquivo de configuração do supervisor encontrado")
            
            # Verificar status do processo
            try:
                result = subprocess.run(['supervisorctl', 'status', 'assessment'],
                                      capture_output=True, text=True)
                if 'RUNNING' in result.stdout:
                    print("✅ Processo assessment está rodando")
                else:
                    print("⚠️ Processo assessment não está rodando")
                    print(f"   Status: {result.stdout.strip()}")
            except:
                print("⚠️ Não foi possível verificar status do supervisor")
        else:
            print("❌ Arquivo de configuração do supervisor não encontrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar supervisor: {e}")
        return False

def verificar_nginx():
    """Verificar configuração do nginx"""
    
    print("🌐 Verificando nginx...")
    
    try:
        # Verificar se nginx está rodando
        result = subprocess.run(['systemctl', 'is-active', 'nginx'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Nginx está ativo")
        else:
            print("⚠️ Nginx não está ativo")
        
        # Verificar configuração do site
        site_config = '/etc/nginx/sites-enabled/assessment'
        if os.path.exists(site_config):
            print("✅ Configuração do site encontrada")
        else:
            print("⚠️ Configuração do site não encontrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar nginx: {e}")
        return False

def gerar_relatorio_final(resultados):
    """Gerar relatório final da verificação"""
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DA VERIFICAÇÃO")
    print("=" * 60)
    
    total_checks = len(resultados)
    checks_ok = sum(1 for result in resultados if result[1])
    
    print(f"✅ Verificações bem-sucedidas: {checks_ok}/{total_checks}")
    print(f"⚠️ Verificações com problemas: {total_checks - checks_ok}/{total_checks}")
    
    print("\n📋 Detalhes:")
    for nome, sucesso in resultados:
        status = "✅" if sucesso else "❌"
        print(f"   {status} {nome}")
    
    if checks_ok == total_checks:
        print("\n🎉 SISTEMA INSTALADO CORRETAMENTE!")
        print("🌐 O sistema está pronto para uso")
    elif checks_ok >= total_checks * 0.8:  # 80% ou mais
        print("\n⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        print("📝 Alguns itens precisam de atenção, mas o sistema pode funcionar")
    else:
        print("\n❌ PROBLEMAS NA INSTALAÇÃO")
        print("📝 Vários itens precisam ser corrigidos")
    
    print("\n📞 Para suporte, consulte a documentação ou entre em contato")
    print("=" * 60)
    
    return checks_ok == total_checks

def main():
    """Função principal de verificação"""
    
    print("=" * 60)
    print("🔍 VERIFICAÇÃO DA INSTALAÇÃO DO SISTEMA")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Lista de verificações
    verificacoes = [
        ("Sistema operacional", verificar_sistema_operacional),
        ("Variáveis de ambiente", verificar_variaveis_ambiente),
        ("Banco de dados", verificar_banco_dados),
        ("Aplicação Flask", verificar_aplicacao_flask),
        ("Permissões de arquivos", verificar_permissoes_arquivos),
        ("Supervisor", verificar_supervisor),
        ("Nginx", verificar_nginx)
    ]
    
    resultados = []
    
    for nome, funcao in verificacoes:
        print(f"📋 {nome}...")
        try:
            resultado = funcao()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ Erro inesperado em {nome}: {e}")
            resultados.append((nome, False))
        print()
    
    # Gerar relatório final
    sucesso_total = gerar_relatorio_final(resultados)
    
    return 0 if sucesso_total else 1

if __name__ == "__main__":
    sys.exit(main())