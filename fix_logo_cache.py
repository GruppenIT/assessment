#!/usr/bin/env python3
"""
Script para forçar atualização do cache do logo do sistema
"""

import sys
import env_loader

def atualizar_logo_cache():
    """Força a atualização do cache do logo"""
    
    try:
        from app import create_app, db
        from models.logo import Logo
        from models.configuracao import Configuracao
        
        app = create_app()
        with app.app_context():
            print("🔄 Verificando status atual do logo...")
            
            # Verificar logo na configuração
            logo_config = Configuracao.get_logo_sistema()
            print(f"Logo na configuração: {logo_config}")
            
            # Verificar logos no modelo
            logos = Logo.query.all()
            print(f"Total de logos no banco: {len(logos)}")
            
            for logo in logos:
                print(f"  ID: {logo.id}, Nome: {logo.nome_arquivo}, Ativo: {logo.ativo}, Caminho: {logo.caminho_arquivo}")
            
            # Encontrar logo ativo
            logo_ativo = Logo.query.filter_by(ativo=True).first()
            
            if logo_ativo:
                print(f"\n✅ Logo ativo encontrado: {logo_ativo.nome_arquivo}")
                print(f"   Caminho: {logo_ativo.caminho_arquivo}")
                
                # Sincronizar com configuração se necessário
                if logo_config != logo_ativo.caminho_arquivo:
                    print("⚠️ Inconsistência detectada! Sincronizando...")
                    Configuracao.set_logo_sistema(logo_ativo.caminho_arquivo)
                    print("✅ Logo sincronizado na configuração")
                else:
                    print("✅ Logo já está sincronizado")
            else:
                print("❌ Nenhum logo ativo encontrado")
                
                # Se há logos mas nenhum ativo, ativar o mais recente
                logo_recente = Logo.query.order_by(Logo.id.desc()).first()
                if logo_recente:
                    print(f"🔄 Ativando logo mais recente: {logo_recente.nome_arquivo}")
                    
                    # Desativar todos
                    Logo.query.update({'ativo': False})
                    
                    # Ativar o mais recente
                    logo_recente.ativo = True
                    
                    # Atualizar configuração
                    Configuracao.set_logo_sistema(logo_recente.caminho_arquivo)
                    
                    db.session.commit()
                    print("✅ Logo reativado com sucesso")
                else:
                    print("❌ Nenhum logo encontrado no sistema")
            
            print("\n" + "="*50)
            print("🎉 VERIFICAÇÃO CONCLUÍDA")
            print("="*50)
            print("📝 Status final:")
            print(f"   Logo ativo: {Logo.query.filter_by(ativo=True).first().nome_arquivo if Logo.query.filter_by(ativo=True).first() else 'Nenhum'}")
            print(f"   Configuração: {Configuracao.get_logo_sistema()}")
            print("\n🔄 Reinicie a aplicação web para ver as mudanças")
            
    except Exception as e:
        print(f"❌ Erro ao verificar logo: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 CORREÇÃO DE CACHE DO LOGO DO SISTEMA")
    print("=" * 50)
    atualizar_logo_cache()