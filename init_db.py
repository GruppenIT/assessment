#!/usr/bin/env python3
"""
Script para inicializar o banco de dados do sistema de assessment
Para uso em ambiente on-premise
"""

import os
import sys
from app import create_app, db

def init_database():
    """Inicializa o banco de dados com tabelas e dados padrão"""
    
    # Criar a aplicação
    app = create_app()
    
    with app.app_context():
        try:
            # Importar todos os modelos para garantir que as tabelas sejam criadas
            from models import usuario, dominio, pergunta, resposta, logo, tipo_assessment, cliente, respondente
            
            print("Criando tabelas do banco de dados...")
            db.create_all()
            print("✓ Tabelas criadas com sucesso!")
            
            # Criar usuário admin padrão se não existir
            from models.usuario import Usuario
            from models.tipo_assessment import TipoAssessment
            from werkzeug.security import generate_password_hash
            
            admin_existente = Usuario.query.filter_by(email='admin@sistema.com').first()
            if not admin_existente:
                print("Criando usuário administrador padrão...")
                admin = Usuario(
                    nome='Administrador',
                    email='admin@sistema.com',
                    senha_hash=generate_password_hash('admin123'),
                    tipo='admin'
                )
                db.session.add(admin)
                print("✓ Usuário admin criado: admin@sistema.com / admin123")
            else:
                print("✓ Usuário admin já existe")
            
            # Criar tipo de assessment padrão se não existir
            tipo_default = TipoAssessment.query.filter_by(nome='Cibersegurança').first()
            if not tipo_default:
                print("Criando tipo de assessment padrão...")
                tipo_default = TipoAssessment(
                    nome='Cibersegurança',
                    descricao='Assessment de maturidade em cibersegurança',
                    ordem=1,
                    ativo=True
                )
                db.session.add(tipo_default)
                print("✓ Tipo de assessment 'Cibersegurança' criado")
            else:
                print("✓ Tipo de assessment 'Cibersegurança' já existe")
            
            db.session.commit()
            print("\n✓ Banco de dados inicializado com sucesso!")
            print("\nCredenciais de acesso administrativo:")
            print("  Email: admin@sistema.com")
            print("  Senha: admin123")
            print("\nO sistema está pronto para uso!")
            
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    init_database()