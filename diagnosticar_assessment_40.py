#!/usr/bin/env python3
from app import app, db
from models.assessment_publico import AssessmentPublico
from models.tipo_assessment import TipoAssessment

with app.app_context():
    print("\n🔍 DIAGNÓSTICO DO ASSESSMENT #40")
    print("=" * 60)
    
    assessment = AssessmentPublico.query.get(40)
    
    if not assessment:
        print("❌ Assessment #40 não encontrado")
    else:
        print(f"✓ Assessment #{assessment.id} encontrado")
        print(f"  tipo_assessment_id: {assessment.tipo_assessment_id}")
        print(f"  tipo_assessment objeto: {assessment.tipo_assessment}")
        
        # Verificar se o tipo existe no banco
        if assessment.tipo_assessment_id:
            tipo = TipoAssessment.query.get(assessment.tipo_assessment_id)
            print(f"  Tipo no banco: {tipo}")
            if tipo:
                print(f"  Nome do tipo: {tipo.nome}")
                print(f"  Email destinatários: {tipo.email_destinatarios}")
        
        print(f"\n📊 Todos os tipos de assessment disponíveis:")
        tipos = TipoAssessment.query.all()
        for tipo in tipos:
            print(f"  #{tipo.id}: {tipo.nome} (emails: {tipo.email_destinatarios or 'NÃO CONFIGURADO'})")
    
    print()
