#!/usr/bin/env python3
"""
Script para gerar requirements.txt baseado nas dependências do projeto
Sistema de Avaliações de Maturidade
"""

import subprocess
import sys

def get_installed_packages():
    """Obtém lista de pacotes instalados"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def filter_project_packages(packages):
    """Filtra apenas os pacotes necessários para o projeto"""
    required_packages = {
        'flask': 'Flask',
        'flask-login': 'Flask-Login', 
        'flask-sqlalchemy': 'Flask-SQLAlchemy',
        'flask-wtf': 'Flask-WTF',
        'wtforms': 'WTForms',
        'email-validator': 'email-validator',
        'psycopg2-binary': 'psycopg2-binary',
        'reportlab': 'reportlab',
        'gunicorn': 'gunicorn',
        'python-dotenv': 'python-dotenv'
    }
    
    project_requirements = []
    
    for package in packages:
        if '==' in package:
            name, version = package.split('==', 1)
            name_lower = name.lower()
            
            if name_lower in required_packages:
                project_requirements.append(package)
    
    # Adicionar pacotes obrigatórios se não encontrados
    found_packages = [req.split('==')[0].lower() for req in project_requirements]
    
    for pkg_key, pkg_name in required_packages.items():
        if pkg_key not in found_packages:
            # Versões mínimas conhecidas
            versions = {
                'Flask': '2.3.3',
                'Flask-Login': '0.6.3',
                'Flask-SQLAlchemy': '3.0.5', 
                'Flask-WTF': '1.1.1',
                'WTForms': '3.0.1',
                'email-validator': '2.0.0',
                'psycopg2-binary': '2.9.7',
                'reportlab': '4.0.4',
                'gunicorn': '21.2.0',
                'python-dotenv': '1.0.0'
            }
            project_requirements.append(f"{pkg_name}>={versions.get(pkg_name, '1.0.0')}")
    
    return sorted(project_requirements)

def main():
    print("🔍 Analisando dependências do projeto...")
    
    installed_packages = get_installed_packages()
    project_packages = filter_project_packages(installed_packages)
    
    requirements_content = """# Requirements para Sistema de Avaliações de Maturidade
# Gruppen Serviços de Informática Ltda

# Core Flask
Flask>=2.3.3
Flask-Login>=0.6.3
Flask-SQLAlchemy>=3.0.5
Flask-WTF>=1.1.1

# Forms and Validation
WTForms>=3.0.1
email-validator>=2.0.0

# Database
psycopg2-binary>=2.9.7

# PDF Generation
reportlab>=4.0.4

# Production Server
gunicorn>=21.2.0

# Environment Management
python-dotenv>=1.0.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    
    print("✅ requirements.txt gerado com sucesso!")
    print("\n📋 Dependências incluídas:")
    for line in requirements_content.split('\n'):
        if line and not line.startswith('#') and line.strip():
            print(f"  - {line}")

if __name__ == '__main__':
    main()