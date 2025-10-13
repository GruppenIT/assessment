#!/usr/bin/env python3
"""
Script de diagnóstico para sistema de e-mail
Verifica configurações SMTP, destinatários e testa envio
"""

import sys
import os

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.parametro_sistema import ParametroSistema
from models.assessment_version import AssessmentTipo
from models.leads import Lead
from utils.email_utils import EmailSender, enviar_alerta_novo_lead

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_status(label, value, ok=True):
    status = "✓" if ok else "✗"
    color = "\033[92m" if ok else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {label}: {value}")

def diagnosticar():
    with app.app_context():
        print("\n🔍 DIAGNÓSTICO DO SISTEMA DE E-MAIL")
        
        # 1. Verificar configurações SMTP
        print_header("1. CONFIGURAÇÕES SMTP")
        
        config = ParametroSistema.get_smtp_config()
        
        if not config:
            print_status("Configurações SMTP", "NÃO ENCONTRADAS", False)
            print("\n❌ Configure o SMTP em: /admin/parametros/smtp")
            return
        
        print_status("Servidor SMTP", config.get('smtp_server', 'NÃO CONFIGURADO'))
        print_status("Porta", config.get('smtp_port', 'NÃO CONFIGURADA'))
        print_status("Tipo de Autenticação", config.get('smtp_auth_type', 'NÃO CONFIGURADA'))
        print_status("E-mail Remetente", config.get('smtp_from_email', 'NÃO CONFIGURADO'))
        print_status("Nome Remetente", config.get('smtp_from_name', 'NÃO CONFIGURADO'))
        
        # Verificar campos específicos por tipo de auth
        auth_type = config.get('smtp_auth_type')
        
        if auth_type == 'basic':
            user_ok = bool(config.get('smtp_user'))
            pass_ok = bool(config.get('smtp_password'))
            print_status("Usuário SMTP", "Configurado" if user_ok else "NÃO CONFIGURADO", user_ok)
            print_status("Senha SMTP", "Configurada" if pass_ok else "NÃO CONFIGURADA", pass_ok)
        elif auth_type == 'oauth2':
            client_id_ok = bool(config.get('smtp_client_id'))
            secret_ok = bool(config.get('smtp_client_secret'))
            token_ok = bool(config.get('smtp_refresh_token'))
            tenant_ok = bool(config.get('smtp_tenant_id'))
            print_status("Client ID", "Configurado" if client_id_ok else "NÃO CONFIGURADO", client_id_ok)
            print_status("Client Secret", "Configurado" if secret_ok else "NÃO CONFIGURADO", secret_ok)
            print_status("Refresh Token", "Configurado" if token_ok else "NÃO CONFIGURADO", token_ok)
            print_status("Tenant ID", "Configurado" if tenant_ok else "NÃO CONFIGURADO", tenant_ok)
        
        # 2. Verificar tipos de assessment com destinatários
        print_header("2. TIPOS DE ASSESSMENT COM NOTIFICAÇÃO")
        
        tipos = AssessmentTipo.query.filter(AssessmentTipo.url_publica == True).all()
        
        if not tipos:
            print_status("Assessments com URL pública", "NENHUM ENCONTRADO", False)
            print("\n❌ Configure assessments com URL pública ativada")
            return
        
        tipos_com_email = []
        for tipo in tipos:
            if tipo.email_destinatarios:
                emails = [e.strip() for e in tipo.email_destinatarios.replace(';', ',').split(',') if e.strip()]
                print_status(f"Assessment: {tipo.nome}", f"{len(emails)} destinatário(s)", True)
                for email in emails:
                    print(f"    → {email}")
                tipos_com_email.append(tipo)
            else:
                print_status(f"Assessment: {tipo.nome}", "SEM DESTINATÁRIOS", False)
        
        if not tipos_com_email:
            print("\n⚠️  Nenhum assessment tem destinatários configurados!")
            print("   Configure em: Assessments → Editar Tipo → E-mails para Notificação")
            return
        
        # 3. Verificar leads criados
        print_header("3. LEADS CRIADOS RECENTEMENTE")
        
        leads_recentes = Lead.query.order_by(Lead.data_criacao.desc()).limit(5).all()
        
        if not leads_recentes:
            print_status("Leads encontrados", "NENHUM", False)
            print("\n⚠️  Nenhum lead foi criado ainda")
            print("   Teste respondendo um assessment público")
        else:
            print_status("Leads encontrados", len(leads_recentes), True)
            for lead in leads_recentes:
                print(f"\n  Lead #{lead.id}:")
                print(f"    Nome: {lead.nome}")
                print(f"    E-mail: {lead.email}")
                print(f"    Assessment: {lead.tipo_assessment.nome if lead.tipo_assessment else 'N/A'}")
                print(f"    Data: {lead.data_criacao}")
                
                # Verificar se tem destinatários
                if lead.tipo_assessment and lead.tipo_assessment.email_destinatarios:
                    print(f"    ✓ Tipo tem destinatários configurados")
                else:
                    print(f"    ✗ Tipo NÃO tem destinatários configurados")
        
        # 4. Teste de envio
        print_header("4. TESTE DE ENVIO")
        
        email_teste = input("\n📧 Digite um e-mail para teste (Enter para pular): ").strip()
        
        if email_teste:
            print(f"\n📤 Enviando e-mail de teste para {email_teste}...")
            
            sender = EmailSender()
            
            corpo_html = """
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #6366f1;">🧪 E-mail de Teste</h2>
                <p>Este é um e-mail de teste do sistema de notificações.</p>
                <p>Se você recebeu esta mensagem, o sistema está configurado corretamente!</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Enviado pelo script de diagnóstico
                </p>
            </body>
            </html>
            """
            
            try:
                resultado = sender.enviar_email(
                    destinatarios=[email_teste],
                    assunto="🧪 Teste - Sistema de E-mail Assessments",
                    corpo_html=corpo_html,
                    corpo_texto="Este é um e-mail de teste. Se você recebeu, está funcionando!"
                )
                
                if resultado:
                    print_status("Envio de teste", "SUCESSO ✓", True)
                    print(f"\n✉️  Verifique a caixa de entrada de {email_teste}")
                    print("   (Pode estar em spam/lixo eletrônico)")
                else:
                    print_status("Envio de teste", "FALHOU ✗", False)
                    print("\n❌ Verifique os logs para mais detalhes")
                    
            except Exception as e:
                print_status("Envio de teste", f"ERRO: {str(e)}", False)
        
        # 5. Recomendações
        print_header("5. RECOMENDAÇÕES")
        
        problemas = []
        
        if not config.get('smtp_server'):
            problemas.append("Configure o servidor SMTP em /admin/parametros/smtp")
        
        if not tipos_com_email:
            problemas.append("Configure destinatários nos tipos de assessment")
        
        if not problemas:
            print("\n✅ Configuração parece correta!")
            print("\nPróximos passos:")
            print("1. Responda um assessment público completo")
            print("2. Verifique a caixa de entrada dos destinatários")
            print("3. Verifique a pasta de spam/lixo eletrônico")
            print("4. Verifique os logs: sudo supervisorctl tail -f assessment stdout")
        else:
            print("\n⚠️  Problemas encontrados:")
            for i, problema in enumerate(problemas, 1):
                print(f"{i}. {problema}")

if __name__ == "__main__":
    try:
        diagnosticar()
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print()
