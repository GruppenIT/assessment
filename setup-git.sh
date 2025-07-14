#!/bin/bash

# Script para configurar Git no projeto
# Sistema de Avaliações de Maturidade

echo "================================================"
echo "Configuração Git - Sistema de Avaliações"
echo "================================================"

# Verificar se git está disponível
if ! command -v git &> /dev/null; then
    echo "❌ Git não está instalado. Instale o git primeiro."
    exit 1
fi

# Configurar Git se necessário
echo "📋 Configurando Git..."

read -p "Digite seu nome para commits: " git_name
read -p "Digite seu email para commits: " git_email

git config --global user.name "$git_name"
git config --global user.email "$git_email"

# Inicializar repositório se necessário
if [ ! -d ".git" ]; then
    echo "🔧 Inicializando repositório Git..."
    git init
    
    # Criar README se não existir
    if [ ! -f "README.md" ]; then
        cat > README.md << EOF
# Sistema de Avaliações de Maturidade

Sistema web completo em Flask para avaliações de maturidade organizacional com múltiplos tipos de assessment.

## Características

- 🏢 **Multi-tenant**: Suporte a múltiplos clientes
- 📊 **Múltiplos Assessments**: Cibersegurança, Compliance, etc.
- 👥 **Sistema de Respondentes**: Múltiplos usuários por cliente
- 📈 **Relatórios Avançados**: Geração de PDFs com gráficos
- 📝 **Importação CSV**: Bulk import de domínios e perguntas
- 🔐 **Autenticação Robusta**: Admin e respondentes separados
- 🎨 **Interface Moderna**: Bootstrap 5 e design responsivo

## Tecnologias

- **Backend**: Flask (Python)
- **Banco**: PostgreSQL
- **Frontend**: Bootstrap 5 + Jinja2
- **Relatórios**: ReportLab
- **Deploy**: Nginx + Gunicorn + Supervisor

## Desenvolvido por

**Gruppen Serviços de Informática Ltda**

## Licença

Todos os direitos reservados © 2025 Gruppen Serviços de Informática Ltda
EOF
    fi
    
    echo "✅ Repositório inicializado"
else
    echo "✅ Repositório Git já existe"
fi

# Configurar .gitignore se necessário
if [ ! -f ".gitignore" ]; then
    echo "📋 Criando .gitignore..."
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
venv/
env/
ENV/
.env

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite

# Uploads
static/uploads/*
!static/uploads/.gitkeep

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Replit specific
.replit
replit.nix
EOF
fi

# Verificar arquivos para commit
echo "📁 Verificando arquivos para commit..."
git add .

# Mostrar status
echo "📊 Status do repositório:"
git status

# Fazer commit inicial se necessário
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "🚀 Fazendo commit inicial..."
    git commit -m "Initial commit - Sistema de Avaliações de Maturidade

- Sistema completo de assessment multi-tipo
- Interface administrativa e de respondentes
- Importação CSV com suporte a acentos
- Geração de relatórios em PDF
- Deploy automatizado para Ubuntu
- Desenvolvido por Gruppen Serviços de Informática Ltda"
    echo "✅ Commit inicial realizado"
fi

echo ""
echo "🎉 Git configurado com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo "1. Criar repositório no GitHub/GitLab"
echo "2. Adicionar remote: git remote add origin <URL_DO_REPO>"
echo "3. Push inicial: git push -u origin main"
echo "4. No servidor: ./deploy.sh install"
echo ""
echo "📝 Para commits futuros:"
echo "   git add ."
echo "   git commit -m 'Descrição das mudanças'"
echo "   git push origin main"
echo "   # No servidor: ./deploy.sh update"