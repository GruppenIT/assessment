#!/usr/bin/env python3
from app import app
from models.assessment_version import AssessmentTipo

with app.app_context():
    print("\n📋 TIPOS DE ASSESSMENT COM URL PÚBLICA:")
    print("=" * 70)
    
    tipos = AssessmentTipo.query.filter(AssessmentTipo.url_publica == True).all()
    
    if not tipos:
        print("❌ Nenhum assessment com URL pública encontrado!")
    else:
        for tipo in tipos:
            print(f"\n📌 {tipo.nome}")
            print(f"   ID: {tipo.id}")
            print(f"   URL Pública: {'✓ Ativada' if tipo.url_publica else '✗ Desativada'}")
            
            if hasattr(tipo, 'email_destinatarios') and tipo.email_destinatarios:
                emails = [e.strip() for e in tipo.email_destinatarios.replace(';', ',').split(',') if e.strip()]
                print(f"   Destinatários: ✓ {len(emails)} configurado(s)")
                for email in emails:
                    print(f"      → {email}")
            else:
                print(f"   Destinatários: ✗ NENHUM CONFIGURADO")
                print(f"   ⚠️  Configure em: Assessments → Editar Tipo (ID {tipo.id})")
    
    print("\n" + "=" * 70)
    print()
