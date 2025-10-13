#!/usr/bin/env python3
"""Diagnostica o assessment público criado para entender por que o lead não foi gerado"""
from app import app
from models.assessment_publico import AssessmentPublico
from models.tipo_assessment import TipoAssessment
from models.lead import Lead

with app.app_context():
    print("\n🔍 DIAGNÓSTICO DO ASSESSMENT CRIADO")
    print("=" * 70)
    
    assessment = AssessmentPublico.query.first()
    
    if not assessment:
        print("❌ Nenhum assessment encontrado")
    else:
        print(f"\n📋 Assessment Público #{assessment.id}")
        print(f"   tipo_assessment_id: {assessment.tipo_assessment_id}")
        print(f"   token: {assessment.token}")
        print(f"   data_inicio: {assessment.data_inicio}")
        print(f"   data_conclusao: {assessment.data_conclusao}")
        
        print(f"\n👤 Dados do Respondente:")
        print(f"   nome: {assessment.nome_respondente or 'NÃO PREENCHIDO'}")
        print(f"   email: {assessment.email_respondente or 'NÃO PREENCHIDO'}")
        print(f"   empresa: {assessment.empresa_respondente or 'NÃO PREENCHIDO'}")
        
        print(f"\n📊 Respostas:")
        print(f"   Total de respostas: {len(assessment.respostas)}")
        
        # Verificar tipo de assessment
        print(f"\n🔍 Tipo de Assessment:")
        if assessment.tipo_assessment:
            print(f"   ✓ Tipo encontrado: {assessment.tipo_assessment.nome}")
            print(f"   ID: {assessment.tipo_assessment.id}")
            print(f"   Email destinatários: {assessment.tipo_assessment.email_destinatarios or 'NÃO CONFIGURADO'}")
        else:
            print(f"   ✗ Tipo NÃO encontrado (tipo_assessment é None)")
            if assessment.tipo_assessment_id:
                tipo = TipoAssessment.query.get(assessment.tipo_assessment_id)
                if tipo:
                    print(f"   ⚠️  Mas encontrado via query direta: {tipo.nome}")
                else:
                    print(f"   ✗ Tipo ID {assessment.tipo_assessment_id} não existe no banco")
        
        # Verificar se tem lead
        lead = Lead.query.filter_by(assessment_publico_id=assessment.id).first()
        print(f"\n🎯 Lead:")
        if lead:
            print(f"   ✓ Lead #{lead.id} encontrado")
        else:
            print(f"   ✗ NENHUM LEAD CRIADO")
            
            # Verificar por que não foi criado
            print(f"\n❓ Possíveis motivos:")
            if not assessment.data_conclusao:
                print(f"   - Assessment não foi concluído (data_conclusao é None)")
            if not assessment.nome_respondente:
                print(f"   - Dados do respondente não foram preenchidos")
            if not assessment.tipo_assessment:
                print(f"   - Tipo de assessment inválido")
    
    print("\n" + "=" * 70 + "\n")
