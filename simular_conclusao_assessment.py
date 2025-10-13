#!/usr/bin/env python3
"""
Simula a conclusão de um assessment público para testar o fluxo de criação de lead e envio de email
"""
import sys
import logging
from datetime import datetime
from app import app, db
from models.assessment_publico import AssessmentPublico
from models.lead import Lead
from models.tipo_assessment import TipoAssessment
from utils.email_utils import enviar_alerta_novo_lead

# Configurar logging para ver tudo
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    with app.app_context():
        print("\n" + "="*70)
        print("🧪 SIMULAÇÃO DE CONCLUSÃO DE ASSESSMENT PÚBLICO")
        print("="*70)
        
        # Buscar um assessment público não concluído
        assessment = AssessmentPublico.query.filter(
            AssessmentPublico.data_conclusao == None
        ).first()
        
        if not assessment:
            print("\n❌ Nenhum assessment público pendente encontrado")
            print("   Crie um novo assessment público com URL pública para testar")
            return
        
        print(f"\n📋 Assessment Público Selecionado: #{assessment.id}")
        print(f"   Tipo: {assessment.tipo_assessment.nome if assessment.tipo_assessment else 'N/A'}")
        print(f"   Token: {assessment.token}")
        
        # Verificar se já tem dados do respondente
        if not assessment.nome_respondente or not assessment.email_respondente:
            print("\n⚠️  Dados do respondente não preenchidos")
            print("   Preenchendo dados de teste...")
            assessment.nome_respondente = "João Silva - TESTE"
            assessment.email_respondente = "teste@exemplo.com"
            assessment.telefone_respondente = "(11) 98888-7777"
            assessment.cargo_respondente = "Diretor de TI"
            assessment.empresa_respondente = "Empresa Teste LTDA"
        
        print(f"\n👤 Respondente: {assessment.nome_respondente}")
        print(f"   Email: {assessment.email_respondente}")
        print(f"   Empresa: {assessment.empresa_respondente}")
        
        # Verificar respostas
        total_respondidas = len(assessment.respostas)
        
        print(f"\n📊 Progresso:")
        print(f"   Respostas registradas: {total_respondidas}")
        
        # Marcar como concluído
        assessment.data_conclusao = datetime.utcnow()
        db.session.commit()
        print(f"\n✓ Assessment marcado como concluído: {assessment.data_conclusao}")
        
        # Verificar se já existe lead
        lead_existente = Lead.query.filter_by(assessment_publico_id=assessment.id).first()
        
        if lead_existente:
            print(f"\n⚠️  Lead já existe: #{lead_existente.id}")
            print(f"   Nome: {lead_existente.nome}")
            print(f"   Email: {lead_existente.email}")
            print("\n   Testando envio de email com lead existente...")
            lead = lead_existente
        else:
            print("\n📝 Criando novo lead...")
            try:
                lead = Lead.criar_de_assessment_publico(assessment)
                db.session.add(lead)
                db.session.commit()
                print(f"   ✓ Lead #{lead.id} criado com sucesso")
            except Exception as e:
                print(f"   ❌ Erro ao criar lead: {str(e)}")
                import traceback
                traceback.print_exc()
                return
        
        # Buscar tipo de assessment
        tipo_assessment = assessment.tipo_assessment
        
        if not tipo_assessment:
            print("\n❌ Tipo de assessment não encontrado!")
            return
        
        print(f"\n📧 Configuração de E-mail:")
        print(f"   Tipo: {tipo_assessment.nome}")
        
        if tipo_assessment.email_destinatarios:
            emails = [e.strip() for e in tipo_assessment.email_destinatarios.replace(';', ',').split(',') if e.strip()]
            print(f"   Destinatários: {len(emails)}")
            for email in emails:
                print(f"      → {email}")
        else:
            print("   ❌ Nenhum destinatário configurado!")
            return
        
        # Tentar enviar e-mail
        print("\n" + "-"*70)
        print("📤 ENVIANDO E-MAIL DE NOTIFICAÇÃO...")
        print("-"*70)
        
        try:
            resultado = enviar_alerta_novo_lead(lead, tipo_assessment)
            
            print("\n" + "="*70)
            if resultado:
                print("✅ E-MAIL ENVIADO COM SUCESSO!")
            else:
                print("❌ FALHA NO ENVIO DO E-MAIL")
                print("   Verifique os logs acima para detalhes")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERRO ao enviar e-mail: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
