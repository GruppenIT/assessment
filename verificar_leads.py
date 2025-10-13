#!/usr/bin/env python3
from app import app
from models.lead import Lead
from models.assessment_publico import AssessmentPublico

with app.app_context():
    print("\n📊 ÚLTIMOS ASSESSMENTS PÚBLICOS E LEADS")
    print("=" * 70)
    
    # Últimos assessments públicos
    assessments = AssessmentPublico.query.order_by(AssessmentPublico.id.desc()).limit(5).all()
    
    for assessment in assessments:
        print(f"\n📋 Assessment Público #{assessment.id}")
        print(f"   Tipo: {assessment.tipo_assessment.nome}")
        print(f"   Respondente: {assessment.nome_respondente or 'NÃO PREENCHIDO'}")
        print(f"   E-mail: {assessment.email_respondente or 'NÃO PREENCHIDO'}")
        print(f"   Conclusão: {assessment.data_conclusao or 'NÃO CONCLUÍDO'}")
        
        # Verificar se tem lead associado
        lead = Lead.query.filter_by(assessment_publico_id=assessment.id).first()
        
        if lead:
            print(f"   ✓ Lead #{lead.id} criado em {lead.data_criacao}")
        else:
            print(f"   ✗ SEM LEAD ASSOCIADO")
            if assessment.data_conclusao:
                print(f"   ⚠️  Assessment concluído mas sem lead!")
    
    print("\n" + "=" * 70)
    print()
