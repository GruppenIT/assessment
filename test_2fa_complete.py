#!/usr/bin/env python3
"""
Teste completo da implementação de 2FA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.usuario import Usuario
from models.respondente import Respondente
from models.two_factor import TwoFactor
from utils.two_factor_utils import (
    get_user_2fa_config, is_2fa_enabled_for_user, 
    reset_user_2fa, check_2fa_required
)
import pyotp

def test_2fa_implementation():
    """Teste completo da implementação 2FA"""
    
    app = create_app()
    
    with app.app_context():
        print("🔐 TESTE COMPLETO - SISTEMA 2FA")
        print("=" * 50)
        
        # 1. Testar criação de configuração para admin
        print("\n1️⃣ TESTANDO ADMIN 2FA")
        admin = Usuario.query.filter_by(email='admin@sistema.com').first()
        if admin:
            config_admin = get_user_2fa_config(admin)
            print(f"   Admin config criada: {'✅' if config_admin else '❌'}")
            
            if config_admin:
                print(f"   Chave secreta: {config_admin.secret_key[:8]}...")
                print(f"   Status ativo: {'✅' if config_admin.is_active else '❌'}")
                print(f"   Códigos backup: {len(config_admin.get_backup_codes_list())} disponíveis")
                
                # Testar geração de QR Code
                try:
                    qr_uri = config_admin.get_totp_uri()
                    print(f"   QR URI gerado: {'✅' if qr_uri else '❌'}")
                    
                    qr_data = config_admin.get_qr_code_data_uri()
                    print(f"   QR Code base64: {'✅' if qr_data.startswith('data:image/png;base64,') else '❌'}")
                except Exception as e:
                    print(f"   ❌ Erro QR Code: {e}")
        
        # 2. Testar verificação de token
        print("\n2️⃣ TESTANDO VERIFICAÇÃO DE TOKEN")
        if config_admin:
            # Gerar token válido usando pyotp
            totp = pyotp.TOTP(config_admin.secret_key)
            current_token = totp.now()
            
            print(f"   Token atual gerado: {current_token}")
            
            # Testar verificação (sem ativar primeiro)
            result = config_admin.verify_token(current_token)
            print(f"   Verificação token: {'✅' if result else '❌'}")
            
            # Testar ativação
            if result:
                config_admin.activate()
                db.session.commit()
                print(f"   2FA ativado: {'✅' if config_admin.is_active else '❌'}")
        
        # 3. Testar códigos de backup
        print("\n3️⃣ TESTANDO CÓDIGOS DE BACKUP")
        if config_admin and config_admin.is_active:
            backup_codes = config_admin.get_backup_codes_list()
            print(f"   Códigos disponíveis: {len(backup_codes)}")
            
            if backup_codes:
                test_backup = backup_codes[0]
                print(f"   Testando código: {test_backup}")
                
                result = config_admin.use_backup_code(test_backup)
                print(f"   Uso código backup: {'✅' if result else '❌'}")
                
                if result:
                    db.session.commit()
                    remaining = len(config_admin.get_backup_codes_list())
                    print(f"   Códigos restantes: {remaining}")
        
        # 4. Testar respondente
        print("\n4️⃣ TESTANDO RESPONDENTE 2FA")
        respondente = Respondente.query.filter_by(ativo=True).first()
        if respondente:
            config_resp = get_user_2fa_config(respondente)
            print(f"   Respondente config: {'✅' if config_resp else '❌'}")
            
            if config_resp:
                print(f"   Status ativo: {'✅' if config_resp.is_active else '❌'}")
                
                # Testar reset administrativo
                print(f"   Testando reset...")
                reset_success = reset_user_2fa(respondente)
                print(f"   Reset executado: {'✅' if reset_success else '❌'}")
                
                if reset_success:
                    db.session.commit()
                    config_resp_new = get_user_2fa_config(respondente)
                    print(f"   Nova config gerada: {'✅' if config_resp_new else '❌'}")
                    print(f"   Nova config inativa: {'✅' if not config_resp_new.is_active else '❌'}")
        
        # 5. Testar utilitários
        print("\n5️⃣ TESTANDO UTILITÁRIOS")
        
        if admin:
            enabled_admin = is_2fa_enabled_for_user(admin)
            print(f"   Admin 2FA enabled: {'✅' if enabled_admin else '❌'}")
            
        if respondente:
            enabled_resp = is_2fa_enabled_for_user(respondente)
            print(f"   Respondente 2FA enabled: {'✅' if not enabled_resp else '❌'} (deve ser False após reset)")
        
        print("\n" + "=" * 50)
        print("🎉 TESTE 2FA CONCLUÍDO")
        
        # 6. Estatísticas finais
        print("\n📊 ESTATÍSTICAS:")
        total_configs = TwoFactor.query.count()
        active_configs = TwoFactor.query.filter_by(is_active=True).count()
        admin_configs = TwoFactor.query.filter(TwoFactor.usuario_id.isnot(None)).count()
        resp_configs = TwoFactor.query.filter(TwoFactor.respondente_id.isnot(None)).count()
        
        print(f"   Total configurações: {total_configs}")
        print(f"   Configurações ativas: {active_configs}")
        print(f"   Configurações admin: {admin_configs}")
        print(f"   Configurações respondentes: {resp_configs}")
        
        return True

if __name__ == "__main__":
    test_2fa_implementation()