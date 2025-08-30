#!/usr/bin/env python3
"""
Script de diagnóstico para identificar erros após deploy onpremise
"""

import sys
import os
import traceback
from datetime import datetime

def diagnosticar_erro():
    """Diagnóstico completo do sistema"""
    
    print("🔍 DIAGNÓSTICO DE ERRO PÓS-DEPLOY")
    print("=" * 50)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar importações básicas
    print("1. 📦 VERIFICANDO IMPORTAÇÕES...")
    try:
        sys.path.append('/var/www/assessment')
        os.chdir('/var/www/assessment')
        
        from app import create_app, db
        print("   ✅ app importado")
        
        from models.usuario import Usuario
        print("   ✅ models.usuario importado")
        
        from models.respondente import Respondente
        print("   ✅ models.respondente importado")
        
        # Verificar se a nova funcionalidade existe
        from forms.cliente_forms import ResponenteForm
        print("   ✅ forms.cliente_forms importado")
        
        form = ResponenteForm()
        if hasattr(form, 'forcar_troca_senha'):
            print("   ✅ Campo forcar_troca_senha existe no formulário")
        else:
            print("   ❌ Campo forcar_troca_senha NÃO encontrado no formulário")
        
    except Exception as e:
        print(f"   ❌ Erro de importação: {e}")
        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False
    
    # 2. Verificar estrutura do banco
    print("\n2. 🗄️ VERIFICANDO ESTRUTURA DO BANCO...")
    try:
        app = create_app()
        with app.app_context():
            from sqlalchemy import text
            
            # Verificar tabela respondentes
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name='respondentes'
                ORDER BY ordinal_position
            """))
            
            colunas = result.fetchall()
            print(f"   📊 Tabela 'respondentes' tem {len(colunas)} colunas:")
            
            tem_forcar_troca = False
            for coluna in colunas:
                nome, tipo, nullable, default = coluna
                if nome == 'forcar_troca_senha':
                    tem_forcar_troca = True
                    print(f"   ✅ {nome}: {tipo} (nullable: {nullable}, default: {default})")
                else:
                    print(f"      {nome}: {tipo}")
            
            if not tem_forcar_troca:
                print("   ❌ Coluna 'forcar_troca_senha' NÃO encontrada!")
            
    except Exception as e:
        print(f"   ❌ Erro no banco: {e}")
        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False
    
    # 3. Verificar modelo Respondente
    print("\n3. 👤 VERIFICANDO MODELO RESPONDENTE...")
    try:
        app = create_app()
        with app.app_context():
            respondente = Respondente.query.first()
            if respondente:
                print(f"   📊 Respondente encontrado: {respondente.nome}")
                
                if hasattr(respondente, 'forcar_troca_senha'):
                    valor = respondente.forcar_troca_senha
                    print(f"   ✅ Campo forcar_troca_senha: {valor}")
                else:
                    print("   ❌ Campo forcar_troca_senha NÃO existe no modelo")
                    
                # Listar todos os atributos
                atributos = [attr for attr in dir(respondente) if not attr.startswith('_')]
                print(f"   📋 Atributos disponíveis: {', '.join(atributos[:10])}...")
            else:
                print("   ⚠️ Nenhum respondente encontrado")
                
    except Exception as e:
        print(f"   ❌ Erro no modelo: {e}")
        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False
    
    # 4. Verificar rotas auth
    print("\n4. 🛣️ VERIFICANDO ROTAS AUTH...")
    try:
        app = create_app()
        with app.app_context():
            from routes.auth import auth_bp
            
            # Listar rotas do blueprint
            rotas = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint and rule.endpoint.startswith('auth.'):
                    rotas.append(rule.endpoint)
            
            print(f"   📊 Rotas auth encontradas: {len(rotas)}")
            
            if 'auth.troca_senha_obrigatoria' in rotas:
                print("   ✅ Rota troca_senha_obrigatoria encontrada")
            else:
                print("   ❌ Rota troca_senha_obrigatoria NÃO encontrada")
                print(f"   📋 Rotas disponíveis: {rotas}")
                
    except Exception as e:
        print(f"   ❌ Erro nas rotas: {e}")
        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False
    
    # 5. Verificar arquivos críticos
    print("\n5. 📄 VERIFICANDO ARQUIVOS CRÍTICOS...")
    arquivos_criticos = [
        'forms/troca_senha_forms.py',
        'templates/auth/troca_senha_obrigatoria.html',
        'routes/auth.py',
        'routes/admin.py',
        'models/respondente.py'
    ]
    
    for arquivo in arquivos_criticos:
        caminho = f'/var/www/assessment/{arquivo}'
        if os.path.exists(caminho):
            tamanho = os.path.getsize(caminho)
            print(f"   ✅ {arquivo} ({tamanho} bytes)")
        else:
            print(f"   ❌ {arquivo} - FALTANDO")
    
    # 6. Teste de criação de app
    print("\n6. 🚀 TESTANDO CRIAÇÃO DE APP...")
    try:
        app = create_app()
        print(f"   ✅ App criado: {type(app)}")
        print(f"   📊 Blueprints: {list(app.blueprints.keys())}")
        
        # Tentar acessar uma rota simples
        with app.test_client() as client:
            response = client.get('/auth/login')
            print(f"   🌐 GET /auth/login: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro na criação do app: {e}")
        print(f"   📋 Traceback: {traceback.format_exc()}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ DIAGNÓSTICO CONCLUÍDO")
    return True

if __name__ == "__main__":
    try:
        diagnosticar_erro()
    except Exception as e:
        print(f"❌ ERRO CRÍTICO NO DIAGNÓSTICO: {e}")
        print(f"📋 Traceback completo:\n{traceback.format_exc()}")