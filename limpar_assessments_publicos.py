#!/usr/bin/env python3
"""
Script para limpar todos os assessments públicos e leads de teste
USO: python limpar_assessments_publicos.py [--confirmar]
"""
import sys
from app import app, db
from models.assessment_publico import AssessmentPublico, RespostaPublica
from models.lead import Lead, LeadHistorico

def main():
    if '--confirmar' not in sys.argv:
        print("\n⚠️  ATENÇÃO: Este script irá EXCLUIR PERMANENTEMENTE:")
        print("   - Todos os assessments públicos")
        print("   - Todas as respostas públicas")
        print("   - Todos os leads")
        print("   - Todo o histórico de leads")
        print("\n   Para confirmar, execute:")
        print("   python limpar_assessments_publicos.py --confirmar")
        print()
        return
    
    with app.app_context():
        print("\n" + "="*70)
        print("🗑️  LIMPEZA COMPLETA DE ASSESSMENTS PÚBLICOS E LEADS")
        print("="*70)
        
        # Contar registros
        total_assessments = AssessmentPublico.query.count()
        total_respostas = RespostaPublica.query.count()
        total_leads = Lead.query.count()
        total_historico = LeadHistorico.query.count()
        
        print(f"\n📊 Registros encontrados:")
        print(f"   Assessments Públicos: {total_assessments}")
        print(f"   Respostas Públicas: {total_respostas}")
        print(f"   Leads: {total_leads}")
        print(f"   Histórico de Leads: {total_historico}")
        
        if total_assessments == 0 and total_leads == 0:
            print("\n✓ Não há dados para limpar")
            return
        
        print("\n🗑️  Excluindo dados...")
        
        # Excluir histórico de leads
        if total_historico > 0:
            LeadHistorico.query.delete()
            print(f"   ✓ {total_historico} registros de histórico excluídos")
        
        # Excluir leads
        if total_leads > 0:
            Lead.query.delete()
            print(f"   ✓ {total_leads} leads excluídos")
        
        # Excluir respostas públicas
        if total_respostas > 0:
            RespostaPublica.query.delete()
            print(f"   ✓ {total_respostas} respostas públicas excluídas")
        
        # Excluir assessments públicos
        if total_assessments > 0:
            AssessmentPublico.query.delete()
            print(f"   ✓ {total_assessments} assessments públicos excluídos")
        
        # Commit
        db.session.commit()
        
        print("\n" + "="*70)
        print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("="*70)
        print("\nAgora você pode criar novos assessments públicos sem conflitos.")
        print()

if __name__ == "__main__":
    main()
