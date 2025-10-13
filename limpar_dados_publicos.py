#!/usr/bin/env python3
"""
Script para limpar todos os dados de assessments públicos e leads
Execute com: python3 limpar_dados_publicos.py
"""

from app import app, db
from models.assessment_publico import AssessmentPublico, RespostaPublica
from models.lead import Lead, LeadHistorico

def limpar_dados():
    """Limpa todos os dados de assessments públicos e leads"""
    
    with app.app_context():
        # Contar registros antes
        print("=" * 60)
        print("DADOS ATUAIS NO SISTEMA")
        print("=" * 60)
        
        total_respostas = RespostaPublica.query.count()
        total_assessments = AssessmentPublico.query.count()
        total_historico = LeadHistorico.query.count()
        total_leads = Lead.query.count()
        
        print(f"Respostas Públicas: {total_respostas}")
        print(f"Assessments Públicos: {total_assessments}")
        print(f"Histórico de Leads: {total_historico}")
        print(f"Leads: {total_leads}")
        print()
        
        if total_respostas == 0 and total_assessments == 0 and total_leads == 0:
            print("✓ Não há dados para limpar!")
            return
        
        # Pedir confirmação
        print("=" * 60)
        print("ATENÇÃO: Esta operação irá DELETAR PERMANENTEMENTE:")
        print("=" * 60)
        print(f"- {total_respostas} respostas públicas")
        print(f"- {total_assessments} assessments públicos")
        print(f"- {total_historico} registros de histórico de leads")
        print(f"- {total_leads} leads")
        print()
        
        confirmacao = input("Digite 'SIM' (em maiúsculas) para confirmar a exclusão: ")
        
        if confirmacao != 'SIM':
            print("\n✗ Operação cancelada pelo usuário")
            return
        
        print("\n" + "=" * 60)
        print("INICIANDO LIMPEZA...")
        print("=" * 60)
        
        try:
            # 1. Deletar respostas públicas primeiro
            if total_respostas > 0:
                print(f"\n[1/4] Deletando {total_respostas} respostas públicas...")
                RespostaPublica.query.delete()
                db.session.commit()
                print("✓ Respostas públicas deletadas")
            
            # 2. Deletar histórico de leads
            if total_historico > 0:
                print(f"\n[2/4] Deletando {total_historico} registros de histórico...")
                LeadHistorico.query.delete()
                db.session.commit()
                print("✓ Histórico de leads deletado")
            
            # 3. Deletar leads
            if total_leads > 0:
                print(f"\n[3/4] Deletando {total_leads} leads...")
                Lead.query.delete()
                db.session.commit()
                print("✓ Leads deletados")
            
            # 4. Deletar assessments públicos
            if total_assessments > 0:
                print(f"\n[4/4] Deletando {total_assessments} assessments públicos...")
                AssessmentPublico.query.delete()
                db.session.commit()
                print("✓ Assessments públicos deletados")
            
            print("\n" + "=" * 60)
            print("LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            
            # Verificar se realmente está vazio
            print("\nVerificação final:")
            print(f"- Respostas Públicas: {RespostaPublica.query.count()}")
            print(f"- Assessments Públicos: {AssessmentPublico.query.count()}")
            print(f"- Histórico de Leads: {LeadHistorico.query.count()}")
            print(f"- Leads: {Lead.query.count()}")
            print("\n✓ Sistema pronto para começar do zero!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ ERRO durante a limpeza: {e}")
            print("Todas as alterações foram revertidas.")
            raise

if __name__ == '__main__':
    limpar_dados()
