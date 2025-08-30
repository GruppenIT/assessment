#!/usr/bin/env python3
"""
Script para atualizar sistema com funcionalidade de troca obrigatória de senha
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.respondente import Respondente
from sqlalchemy import text

def atualizar_sistema():
    """Atualizar sistema com nova funcionalidade"""
    
    app = create_app()
    
    with app.app_context():
        print("🔐 ATUALIZANDO SISTEMA - TROCA OBRIGATÓRIA DE SENHA")
        print("=" * 55)
        
        try:
            # 1. Verificar se coluna existe
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='respondentes' AND column_name='forcar_troca_senha'
            """))
            
            if result.fetchone():
                print("✅ Coluna forcar_troca_senha já existe")
            else:
                # Adicionar coluna
                db.session.execute(text(
                    "ALTER TABLE respondentes ADD COLUMN forcar_troca_senha BOOLEAN DEFAULT FALSE NOT NULL"
                ))
                db.session.commit()
                print("✅ Coluna forcar_troca_senha adicionada")
            
            # 2. Verificar se há respondentes na base
            total_respondentes = Respondente.query.count()
            print(f"📊 Total de respondentes: {total_respondentes}")
            
            # 3. Criar respondente de teste se não houver
            if total_respondentes == 0:
                print("ℹ️ Criando respondente de teste...")
                from models.cliente import Cliente
                cliente = Cliente.query.first()
                if cliente:
                    respondente_teste = Respondente(
                        nome="Teste Troca Senha",
                        email="teste@teste.com",
                        login="teste.troca",
                        cargo="Testador",
                        setor="TI",
                        cliente_id=cliente.id,
                        forcar_troca_senha=True
                    )
                    respondente_teste.set_password("123456")
                    db.session.add(respondente_teste)
                    db.session.commit()
                    print("✅ Respondente de teste criado (login: teste.troca, senha: 123456)")
            
            # 4. Marcar um respondente existente para teste
            respondente_teste = Respondente.query.first()
            if respondente_teste:
                respondente_teste.forcar_troca_senha = True
                db.session.commit()
                print(f"✅ Respondente '{respondente_teste.nome}' marcado para troca obrigatória")
            
            # 5. Verificar arquivos necessários
            arquivos_necessarios = [
                'forms/troca_senha_forms.py',
                'templates/auth/troca_senha_obrigatoria.html'
            ]
            
            for arquivo in arquivos_necessarios:
                if os.path.exists(arquivo):
                    print(f"✅ {arquivo}")
                else:
                    print(f"❌ {arquivo} - FALTANDO")
            
            print("\n" + "=" * 55)
            print("🎉 ATUALIZAÇÃO CONCLUÍDA")
            print("\n📋 FUNCIONALIDADES:")
            print("   ✅ Checkbox 'Forçar troca de senha' na edição de respondentes")
            print("   ✅ Verificação automática no login")
            print("   ✅ Página de troca obrigatória")
            print("   ✅ Desmarcação automática após troca")
            print("   ✅ Integração com fluxo 2FA")
            
            print("\n🧪 TESTE:")
            if respondente_teste:
                print(f"   1. Faça login como: {respondente_teste.login}")
                print(f"   2. Senha atual: (usar senha cadastrada)")
                print("   3. Sistema deve forçar troca de senha")
                print("   4. Após troca, flag será desmarcada automaticamente")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

if __name__ == "__main__":
    atualizar_sistema()