#!/usr/bin/env python3
"""
Script simples para testar envio de e-mail
Uso: python3 testar_email.py seu-email@exemplo.com
"""

import sys
from app import app
from utils.email_utils import EmailSender

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python3 testar_email.py seu-email@exemplo.com")
        sys.exit(1)
    
    email_teste = sys.argv[1]
    
    print(f"\n📤 Enviando e-mail de teste para: {email_teste}")
    print("-" * 50)
    
    with app.app_context():
        sender = EmailSender()
        
        corpo_html = '''
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #6366f1;">✅ Teste de E-mail</h2>
            <p>Este é um e-mail de teste do sistema de assessments.</p>
            <p>Se você recebeu esta mensagem, o sistema está funcionando corretamente!</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                Enviado via teste manual
            </p>
        </body>
        </html>
        '''
        
        resultado = sender.enviar_email(
            destinatarios=[email_teste],
            assunto='🧪 Teste - Sistema de E-mail',
            corpo_html=corpo_html,
            corpo_texto='Teste de e-mail - Se recebeu, está funcionando!'
        )
        
        print()
        if resultado:
            print("✅ E-MAIL ENVIADO COM SUCESSO!")
            print(f"   Verifique a caixa de entrada de: {email_teste}")
            print("   (Pode estar em spam/lixo eletrônico)")
        else:
            print("❌ FALHA NO ENVIO")
            print("   Verifique os logs para mais detalhes:")
            print("   sudo supervisorctl tail -f assessment stdout")
        print()

if __name__ == "__main__":
    main()
