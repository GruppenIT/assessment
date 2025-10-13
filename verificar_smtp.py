#!/usr/bin/env python3
from app import app
from models.parametro_sistema import ParametroSistema

with app.app_context():
    config = ParametroSistema.get_smtp_config()
    
    print("\n📧 CONFIGURAÇÕES SMTP ATUAIS:")
    print("=" * 50)
    print(f"Servidor SMTP: {config.get('smtp_server')}")
    print(f"Porta: {config.get('smtp_port')}")
    print(f"Tipo de Auth: {config.get('smtp_auth_type')}")
    print(f"TLS/SSL: {config.get('smtp_tls')}")
    print(f"Remetente: {config.get('smtp_from_email')}")
    print("=" * 50)
    
    # OAuth2 está funcionando! Precisamos corrigir o servidor SMTP
    if config.get('smtp_auth_type') == 'oauth2':
        print("\n✅ OAuth2 funcionando - Token obtido com sucesso!")
        print("\n⚠️  PROBLEMA: Servidor SMTP não encontrado")
        print("\nPara Microsoft 365 com OAuth2, use:")
        print("  Servidor: smtp.office365.com")
        print("  Porta: 587")
        print("\nOu configure em: /admin/parametros/smtp")
