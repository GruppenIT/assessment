#!/usr/bin/env python3
"""
Script para migrar e atualizar a estrutura do banco de dados
Executa migrações necessárias para novas versões do sistema
"""

import os
import sys
from datetime import datetime

# Carregar variáveis de ambiente
import env_loader

def executar_migracao_basica():
    """Executar migração básica criando/atualizando todas as tabelas"""
    
    print("🔄 Executando migração básica...")
    
    try:
        from app import create_app, db
        
        # Importar todos os modelos para garantir que sejam criados
        import models.usuario
        import models.cliente
        import models.respondente
        import models.tipo_assessment
        import models.dominio
        import models.pergunta
        import models.resposta
        import models.projeto
        import models.auditoria
        import models.configuracao
        import models.logo
        import models.assessment_versioning
        
        app = create_app()
        
        with app.app_context():
            # Criar todas as tabelas que não existem
            db.create_all()
            print("✅ Estrutura básica do banco atualizada")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na migração básica: {e}")
        return False

def verificar_tabela_auditoria():
    """Verificar e criar tabela de auditoria se necessário"""
    
    print("🔍 Verificando tabela de auditoria...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        
        with app.app_context():
            # Verificar se tabela auditoria existe
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'auditoria'
                )
            """)).fetchone()
            
            if result[0]:
                print("✅ Tabela auditoria já existe")
                return True
            
            # Criar tabela auditoria manualmente
            print("🏗️ Criando tabela auditoria...")
            
            db.session.execute(db.text("""
                CREATE TABLE auditoria (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER,
                    acao VARCHAR(50) NOT NULL,
                    tabela VARCHAR(50) NOT NULL,
                    registro_id INTEGER,
                    dados_anteriores TEXT,
                    dados_novos TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Criar índices
            db.session.execute(db.text("""
                CREATE INDEX idx_auditoria_timestamp ON auditoria(timestamp)
            """))
            
            db.session.execute(db.text("""
                CREATE INDEX idx_auditoria_usuario ON auditoria(usuario_id)
            """))
            
            db.session.execute(db.text("""
                CREATE INDEX idx_auditoria_tabela ON auditoria(tabela)
            """))
            
            db.session.commit()
            print("✅ Tabela auditoria criada com sucesso")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar/criar tabela auditoria: {e}")
        return False

def atualizar_configuracoes():
    """Atualizar/criar configurações do sistema"""
    
    print("⚙️ Atualizando configurações do sistema...")
    
    try:
        from app import create_app, db
        from models.configuracao import Configuracao
        
        app = create_app()
        
        with app.app_context():
            configuracoes_atualizadas = [
                {
                    'chave': 'versao_sistema',
                    'valor': '2.1',
                    'descricao': 'Versão atual do sistema'
                },
                {
                    'chave': 'data_ultima_atualizacao',
                    'valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'descricao': 'Data da última atualização do sistema'
                },
                {
                    'chave': 'timezone',
                    'valor': 'America/Sao_Paulo',
                    'descricao': 'Timezone padrão do sistema'
                },
                {
                    'chave': 'max_upload_size',
                    'valor': '16777216',  # 16MB
                    'descricao': 'Tamanho máximo para upload de arquivos (bytes)'
                }
            ]
            
            configuracoes_criadas = 0
            configuracoes_atualizadas_count = 0
            
            for config_data in configuracoes_atualizadas:
                config = Configuracao.query.filter_by(chave=config_data['chave']).first()
                
                if config:
                    # Atualizar configuração existente
                    config.valor = config_data['valor']
                    config.descricao = config_data['descricao']
                    configuracoes_atualizadas_count += 1
                else:
                    # Criar nova configuração
                    nova_config = Configuracao(
                        chave=config_data['chave'],
                        valor=config_data['valor'],
                        descricao=config_data['descricao']
                    )
                    db.session.add(nova_config)
                    configuracoes_criadas += 1
            
            db.session.commit()
            
            print(f"✅ {configuracoes_criadas} configurações criadas")
            print(f"✅ {configuracoes_atualizadas_count} configurações atualizadas")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao atualizar configurações: {e}")
        return False

def verificar_integridade_dados():
    """Verificar integridade dos dados após migração"""
    
    print("🔍 Verificando integridade dos dados...")
    
    try:
        from app import create_app, db
        from models.usuario import Usuario
        from models.configuracao import Configuracao
        
        app = create_app()
        
        with app.app_context():
            # Verificar se usuário admin existe
            admin = Usuario.query.filter_by(email='admin@sistema.com').first()
            if not admin:
                print("⚠️ Usuário admin não encontrado, pode precisar executar instalar_sistema.py")
            else:
                print("✅ Usuário admin encontrado")
            
            # Verificar configurações essenciais
            configs_essenciais = ['nome_sistema', 'versao_sistema', 'timezone']
            configs_encontradas = 0
            
            for config_key in configs_essenciais:
                config = Configuracao.query.filter_by(chave=config_key).first()
                if config:
                    configs_encontradas += 1
            
            print(f"✅ {configs_encontradas}/{len(configs_essenciais)} configurações essenciais encontradas")
            
            # Contar registros principais
            total_usuarios = Usuario.query.count()
            total_configs = Configuracao.query.count()
            
            print(f"📊 Dados no sistema:")
            print(f"   👤 Usuários: {total_usuarios}")
            print(f"   ⚙️ Configurações: {total_configs}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar integridade: {e}")
        return False

def main():
    """Função principal de migração"""
    
    print("=" * 60)
    print("🔄 MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Verificar conectividade
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            if result[0] != 1:
                raise Exception("Teste de conectividade falhou")
        print("✅ Conectividade com banco verificada")
    except Exception as e:
        print(f"❌ Erro de conectividade: {e}")
        return 1
    
    print()
    
    # Executar migrações
    migracoes = [
        ("Migração básica", executar_migracao_basica),
        ("Tabela auditoria", verificar_tabela_auditoria),
        ("Configurações do sistema", atualizar_configuracoes),
        ("Verificar integridade", verificar_integridade_dados)
    ]
    
    for nome, funcao in migracoes:
        print(f"📋 {nome}...")
        if not funcao():
            print(f"\n❌ Falha em: {nome}")
            return 1
        print()
    
    print("=" * 60)
    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("✅ Estrutura do banco atualizada")
    print("✅ Dados verificados")
    print("📝 Sistema pronto para uso")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())