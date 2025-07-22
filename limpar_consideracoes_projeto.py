#!/usr/bin/env python3
"""
Script para limpar considerações finais de um projeto específico
"""

import sys
import env_loader

def listar_projetos():
    """Lista todos os projetos disponíveis"""
    
    try:
        from app import create_app
        from models.projeto import Projeto
        
        app = create_app()
        with app.app_context():
            projetos = Projeto.query.order_by(Projeto.data_criacao.desc()).all()
            
            if not projetos:
                print("❌ Nenhum projeto encontrado no sistema")
                return []
            
            print("📋 Projetos disponíveis:")
            print("-" * 80)
            for projeto in projetos:
                cliente_nome = projeto.cliente.razao_social if projeto.cliente else "Cliente não encontrado"
                tem_consideracoes = "✅" if projeto.consideracoes_finais_ia else "❌"
                
                print(f"ID: {projeto.id:3d} | {projeto.nome:30s} | Cliente: {cliente_nome:20s} | Considerações: {tem_consideracoes}")
            
            print("-" * 80)
            return projetos
            
    except Exception as e:
        print(f"❌ Erro ao listar projetos: {e}")
        return []

def limpar_consideracoes_projeto(projeto_id):
    """Limpa as considerações finais de um projeto específico"""
    
    try:
        from app import create_app, db
        from models.projeto import Projeto
        
        app = create_app()
        with app.app_context():
            projeto = Projeto.query.get(projeto_id)
            
            if not projeto:
                print(f"❌ Projeto com ID {projeto_id} não encontrado")
                return False
            
            print(f"📋 Projeto selecionado:")
            print(f"   ID: {projeto.id}")
            print(f"   Nome: {projeto.nome}")
            print(f"   Cliente: {projeto.cliente.razao_social if projeto.cliente else 'N/A'}")
            
            # Verificar se tem considerações
            if not projeto.consideracoes_finais_ia:
                print("⚠️ Este projeto não possui considerações finais para limpar")
                return True
            
            print(f"   Considerações atuais: {len(projeto.consideracoes_finais_ia)} caracteres")
            print()
            
            # Confirmar operação
            resposta = input("Confirma a limpeza das considerações finais? (s/N): ").lower().strip()
            if resposta != 's':
                print("Operação cancelada")
                return False
            
            # Limpar considerações
            projeto.consideracoes_finais_ia = None
            
            try:
                db.session.commit()
                print("✅ Considerações finais removidas com sucesso!")
                print("📝 O botão 'Gerar Considerações Finais' voltará a aparecer na interface")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao salvar no banco: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Erro ao limpar considerações: {e}")
        return False

def limpar_analises_dominios_projeto(projeto_id):
    """Limpa também as análises dos domínios (opcional)"""
    
    try:
        from app import create_app, db
        from models.projeto import Projeto
        
        app = create_app()
        with app.app_context():
            projeto = Projeto.query.get(projeto_id)
            
            if not projeto:
                return False
            
            # Verificar se tem análises de domínios
            if not projeto.analises_dominios_ia:
                print("⚠️ Este projeto não possui análises de domínios para limpar")
                return True
            
            print(f"📊 Encontradas análises de domínios: {len(projeto.analises_dominios_ia)} caracteres")
            
            resposta = input("Deseja limpar também as análises dos domínios? (s/N): ").lower().strip()
            if resposta != 's':
                return True
            
            # Limpar análises
            projeto.analises_dominios_ia = None
            
            try:
                db.session.commit()
                print("✅ Análises dos domínios também removidas!")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao limpar análises: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Erro ao limpar análises dos domínios: {e}")
        return False

def metodo_sql_direto():
    """Mostra como fazer via SQL direto"""
    
    print()
    print("=" * 80)
    print("🔧 MÉTODO ALTERNATIVO: SQL DIRETO")
    print("=" * 80)
    print()
    print("Se preferir usar SQL diretamente no PostgreSQL:")
    print()
    print("1. Conectar ao banco:")
    print("   psql -h localhost -U assessment_user assessment_db")
    print()
    print("2. Listar projetos:")
    print("   SELECT id, nome, cliente_id, ")
    print("          CASE WHEN consideracoes_finais_ia IS NOT NULL THEN 'SIM' ELSE 'NÃO' END as tem_consideracoes")
    print("   FROM projetos ORDER BY data_criacao DESC;")
    print()
    print("3. Limpar considerações de um projeto específico (substitua X pelo ID):")
    print("   UPDATE projetos SET consideracoes_finais_ia = NULL WHERE id = X;")
    print()
    print("4. Opcional - Limpar também análises de domínios:")
    print("   UPDATE projetos SET analises_dominios_ia = NULL WHERE id = X;")
    print()
    print("5. Verificar resultado:")
    print("   SELECT id, nome, ")
    print("          CASE WHEN consideracoes_finais_ia IS NOT NULL THEN 'SIM' ELSE 'NÃO' END as tem_consideracoes")
    print("   FROM projetos WHERE id = X;")
    print("=" * 80)

def main():
    """Função principal"""
    
    print("=" * 80)
    print("🗑️ LIMPEZA DE CONSIDERAÇÕES FINAIS - PROJETO ESPECÍFICO")
    print("=" * 80)
    print()
    
    # Mostrar opções
    print("Escolha uma opção:")
    print("1. Script automatizado (recomendado)")
    print("2. Comandos SQL diretos")
    print()
    
    opcao = input("Digite sua escolha (1 ou 2): ").strip()
    
    if opcao == "2":
        metodo_sql_direto()
        return 0
    elif opcao != "1":
        print("❌ Opção inválida")
        return 1
    
    # Listar projetos
    projetos = listar_projetos()
    if not projetos:
        return 1
    
    print()
    
    # Solicitar ID do projeto
    try:
        projeto_id = input("Digite o ID do projeto para limpar considerações finais: ").strip()
        projeto_id = int(projeto_id)
    except ValueError:
        print("❌ ID inválido. Digite apenas números.")
        return 1
    
    print()
    
    # Limpar considerações finais
    if not limpar_consideracoes_projeto(projeto_id):
        return 1
    
    print()
    
    # Opção de limpar análises de domínios também
    limpar_analises_dominios_projeto(projeto_id)
    
    print()
    print("=" * 80)
    print("🎉 OPERAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print("📝 Acesse a interface do projeto para:")
    print("   1. Gerar novamente as análises dos domínios (se necessário)")
    print("   2. Gerar novas considerações finais")
    print("   3. O botão 'Gerar Considerações Finais' estará visível novamente")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())