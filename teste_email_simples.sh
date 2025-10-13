#!/bin/bash
# Script para testar envio de e-mail no ambiente on-premise
# Usa o mesmo ambiente Python que a aplicação

echo "🧪 Teste de Envio de E-mail"
echo "======================================"

# Encontrar o Python correto
PYTHON_CMD=""

# Tentar ambiente virtual
if [ -d "venv" ]; then
    PYTHON_CMD="venv/bin/python"
    echo "✓ Usando ambiente virtual: venv"
elif [ -d ".venv" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "✓ Usando ambiente virtual: .venv"
elif [ -d "env" ]; then
    PYTHON_CMD="env/bin/python"
    echo "✓ Usando ambiente virtual: env"
else
    # Tentar python3 direto
    PYTHON_CMD="python3"
    echo "⚠ Usando Python3 global"
fi

echo ""
echo "Digite o e-mail para teste:"
read EMAIL_TESTE

if [ -z "$EMAIL_TESTE" ]; then
    echo "❌ E-mail não informado"
    exit 1
fi

echo ""
echo "📤 Enviando e-mail de teste para: $EMAIL_TESTE"
echo ""

$PYTHON_CMD <<EOF
import sys
import os

# Não usar dotenv aqui, o app.py já carrega
from app import app
from utils.email_utils import EmailSender

with app.app_context():
    sender = EmailSender()
    
    print("Tentando enviar e-mail...")
    
    resultado = sender.enviar_email(
        destinatarios=['$EMAIL_TESTE'],
        assunto='🧪 Teste - Sistema de E-mail',
        corpo_html='''
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
        ''',
        corpo_texto='Teste de e-mail - Se recebeu, está funcionando!'
    )
    
    if resultado:
        print("\n✅ E-MAIL ENVIADO COM SUCESSO!")
        print(f"   Verifique a caixa de entrada de: {EMAIL_TESTE}")
        print("   (Pode estar em spam/lixo eletrônico)")
    else:
        print("\n❌ FALHA NO ENVIO")
        print("   Verifique os logs para mais detalhes:")
        print("   sudo supervisorctl tail -f assessment stdout")
EOF

echo ""
echo "======================================"
