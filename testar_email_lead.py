#!/usr/bin/env python3
"""
Testa envio de e-mail para um lead específico
"""
import sys
from app import app
from models.lead import Lead
from utils.email_utils import enviar_alerta_novo_lead

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python3 testar_email_lead.py <lead_id>")
        sys.exit(1)
    
    lead_id = int(sys.argv[1])
    
    with app.app_context():
        lead = Lead.query.get(lead_id)
        
        if not lead:
            print(f"❌ Lead #{lead_id} não encontrado")
            sys.exit(1)
        
        print(f"\n📧 TESTE DE E-MAIL PARA LEAD")
        print("=" * 60)
        print(f"Lead ID: {lead.id}")
        print(f"Nome: {lead.nome}")
        print(f"E-mail: {lead.email}")
        print(f"Telefone: {lead.telefone}")
        print(f"Empresa: {lead.empresa}")
        
        # Verificar tipo de assessment
        if not lead.tipo_assessment:
            print("\n❌ ERRO: Este lead não tem tipo_assessment associado!")
            print("   Isso impede o envio de e-mail.")
            print("\nVerificando assessment_publico...")
            
            if lead.assessment_publico:
                print(f"   Assessment Público ID: {lead.assessment_publico.id}")
                print(f"   Tipo Assessment ID: {lead.assessment_publico.tipo_assessment_id}")
                
                if lead.assessment_publico.tipo_assessment:
                    print(f"   ✓ Tipo encontrado: {lead.assessment_publico.tipo_assessment.nome}")
                    tipo_assessment = lead.assessment_publico.tipo_assessment
                else:
                    print("   ✗ tipo_assessment também é None no assessment_publico")
                    sys.exit(1)
            else:
                print("   ✗ Assessment público também não existe")
                sys.exit(1)
        else:
            tipo_assessment = lead.tipo_assessment
            print(f"Tipo Assessment: {tipo_assessment.nome}")
        
        # Verificar destinatários
        if tipo_assessment.email_destinatarios:
            emails = [e.strip() for e in tipo_assessment.email_destinatarios.replace(';', ',').split(',') if e.strip()]
            print(f"\n✓ Destinatários configurados: {len(emails)}")
            for email in emails:
                print(f"   → {email}")
        else:
            print("\n❌ Nenhum destinatário configurado para este tipo de assessment")
            sys.exit(1)
        
        # Tentar enviar
        print("\n📤 Enviando e-mail de teste...")
        print("-" * 60)
        
        try:
            resultado = enviar_alerta_novo_lead(lead, tipo_assessment)
            
            if resultado:
                print("\n✅ E-MAIL ENVIADO COM SUCESSO!")
            else:
                print("\n❌ FALHA NO ENVIO")
                print("   Verifique os logs acima para detalhes")
        except Exception as e:
            print(f"\n❌ ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()

if __name__ == "__main__":
    main()
