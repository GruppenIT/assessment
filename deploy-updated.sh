#!/bin/bash

# Script de Deploy Atualizado para Sistema de Avaliações de Maturidade v2.0
# Inclui suporte a todas as novas funcionalidades: AI, gráficos, versioning, etc.
# Deploy para servidor Ubuntu com Nginx + Supervisor

set -e  # Parar em caso de erro

echo "=== DEPLOY SISTEMA DE AVALIAÇÕES DE MATURIDADE v2.0 ==="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
REPO_URL="https://github.com/GruppenIT/assessment.git"
DEPLOY_DIR="/var/www/assessment"
BACKUP_DIR="/var/backups/assessment"

# Função para log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERRO: $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] AVISO: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Verificar dependências do sistema
check_dependencies() {
    log "Verificando dependências do sistema..."
    
    # Python 3.11+
    if ! command -v python3 &> /dev/null; then
        error "Python 3 não encontrado. Instale: sudo apt install python3 python3-venv python3-dev python3-pip"
    fi
    
    # PostgreSQL
    if ! command -v psql &> /dev/null; then
        error "PostgreSQL não encontrado. Instale: sudo apt install postgresql postgresql-contrib"
    fi
    
    # Git
    if ! command -v git &> /dev/null; then
        error "Git não encontrado. Instale: sudo apt install git"
    fi
    
    # Dependências para matplotlib/numpy (novas funcionalidades)
    info "Verificando dependências para gráficos radar..."
    if ! dpkg -l | grep -q python3-dev; then
        warning "python3-dev não encontrado. Recomendado: sudo apt install python3-dev"
    fi
    if ! dpkg -l | grep -q build-essential; then
        warning "build-essential não encontrado. Recomendado: sudo apt install build-essential"
    fi
    if ! dpkg -l | grep -q pkg-config; then
        warning "pkg-config não encontrado. Recomendado: sudo apt install pkg-config"
    fi
    
    # Dependências adicionais para matplotlib
    info "Instalando dependências para matplotlib se necessário..."
    sudo apt-get update -qq
    sudo apt-get install -y python3-dev build-essential pkg-config libfreetype6-dev libpng-dev 2>/dev/null || warning "Algumas dependências podem ter falhado"
    
    log "Dependências verificadas!"
}

# Fazer backup
backup_current() {
    if [ -d "$DEPLOY_DIR" ]; then
        log "Fazendo backup da aplicação atual..."
        sudo mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
        sudo cp -r "$DEPLOY_DIR" "$BACKUP_DIR/$BACKUP_NAME"
        log "Backup criado: $BACKUP_DIR/$BACKUP_NAME"
    fi
}

# Reset completo baseado no script original
reset_and_deploy() {
    log "Executando reset completo e deploy..."
    
    # Parar serviços
    sudo supervisorctl stop assessment 2>/dev/null || true
    
    # Reset banco PostgreSQL
    log "Resetando banco de dados..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS assessment_db;" || warning "Falha ao dropar banco"
    sudo -u postgres psql -c "CREATE DATABASE assessment_db OWNER assessment_user;" || error "Falha ao criar banco"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE assessment_db TO assessment_user;" || warning "Falha ao conceder privilégios"
    
    # Remover diretório atual
    cd /var/www
    sudo rm -rf assessment/ || true
    
    # Clone repositório
    log "Clonando repositório..."
    sudo git clone "$REPO_URL" || error "Falha ao clonar repositório"
    cd "$DEPLOY_DIR"
    
    # Copiar arquivo .env
    if [ -f "/home/suporte/.env" ]; then
        sudo cp /home/suporte/.env ./ || error "Falha ao copiar .env"
        log "Arquivo .env copiado"
    else
        error "Arquivo .env não encontrado em /home/suporte/.env"
    fi
    
    log "Reset e clone concluídos!"
}

# Configurar ambiente Python com novas dependências
setup_python_env() {
    log "Configurando ambiente Python com NOVAS DEPENDÊNCIAS..."
    cd "$DEPLOY_DIR"
    
    # Criar ambiente virtual
    sudo python3 -m venv venv || error "Falha ao criar venv"
    
    # Ativar e atualizar pip
    sudo bash -c "source venv/bin/activate && pip install --upgrade pip" || error "Falha ao atualizar pip"
    
    # Instalar dependências com timeout maior para matplotlib/numpy
    log "Instalando dependências Python (PODE DEMORAR para matplotlib/numpy)..."
    sudo bash -c "source venv/bin/activate && pip install --timeout=300 -r requirements.txt" || error "Falha ao instalar dependências"
    
    # Verificar instalação das novas dependências
    log "Verificando novas dependências instaladas..."
    sudo bash -c "source venv/bin/activate && python -c 'import matplotlib; print(\"✓ Matplotlib instalado:\", matplotlib.__version__)'" || warning "Problema com matplotlib"
    sudo bash -c "source venv/bin/activate && python -c 'import numpy; print(\"✓ NumPy instalado:\", numpy.__version__)'" || warning "Problema com numpy"
    sudo bash -c "source venv/bin/activate && python -c 'import openai; print(\"✓ OpenAI instalado:\", openai.__version__)'" || warning "Problema com openai"
    sudo bash -c "source venv/bin/activate && python -c 'import pytz; print(\"✓ PyTZ instalado:\", pytz.__version__)'" || warning "Problema com pytz"
    
    log "Ambiente Python configurado com TODAS as novas dependências!"
}

# Inicializar banco
initialize_database() {
    log "Inicializando banco de dados..."
    cd "$DEPLOY_DIR"
    sudo bash -c "source venv/bin/activate && python init_db.py" || error "Falha ao inicializar banco"
    log "Banco inicializado!"
}

# Configurar permissões
setup_permissions() {
    log "Configurando permissões..."
    
    sudo chown -R www-data:www-data "$DEPLOY_DIR" || error "Falha ao configurar proprietário"
    sudo chmod -R 755 "$DEPLOY_DIR" || error "Falha ao configurar permissões"
    
    # Permissões especiais para uploads e novos recursos
    sudo mkdir -p "$DEPLOY_DIR/static/uploads/logos"
    sudo chmod -R 775 "$DEPLOY_DIR/static/uploads"
    
    # Diretório para arquivos temporários do matplotlib (gráficos radar)
    sudo mkdir -p /tmp/matplotlib
    sudo chmod 777 /tmp/matplotlib
    
    log "Permissões configuradas!"
}

# Reiniciar serviços
restart_services() {
    log "Reiniciando serviços..."
    
    # Nginx
    sudo nginx -t || error "Configuração Nginx inválida"
    sudo systemctl restart nginx || error "Falha ao reiniciar Nginx"
    
    # Supervisor
    sudo supervisorctl reread || warning "Falha ao ler configuração supervisor"
    sudo supervisorctl update || warning "Falha ao atualizar supervisor"
    sudo supervisorctl restart assessment || error "Falha ao reiniciar aplicação"
    
    log "Serviços reiniciados!"
}

# Verificar saúde
health_check() {
    log "Verificando saúde da aplicação..."
    
    # Aguardar inicialização
    sleep 10
    
    # Verificar processo
    if pgrep -f "gunicorn.*assessment" > /dev/null; then
        log "✓ Processo rodando!"
    else
        warning "✗ Processo não encontrado"
    fi
    
    # Verificar supervisor
    if sudo supervisorctl status assessment | grep -q RUNNING; then
        log "✓ Supervisor OK!"
    else
        warning "✗ Supervisor com problema"
    fi
    
    # Mostrar logs recentes
    info "Últimas linhas do log:"
    sudo tail -n 5 /var/log/supervisor/assessment.log 2>/dev/null || warning "Não foi possível ler logs"
}

# Informações pós-deploy
post_deploy_info() {
    echo ""
    log "=== DEPLOY CONCLUÍDO COM SUCESSO! ==="
    echo ""
    
    info "📁 Aplicação: $DEPLOY_DIR"
    info "🗄️  Banco: assessment_db (PostgreSQL)"
    info "🔧 Serviço: assessment (supervisor)"
    info "🌐 Web: nginx"
    
    echo ""
    info "🆕 NOVAS FUNCIONALIDADES INCLUÍDAS NESTE DEPLOY:"
    info "   ✓ Gráficos radar em relatórios PDF (matplotlib + numpy)"
    info "   ✓ Integração OpenAI para análises inteligentes"
    info "   ✓ Sistema de versionamento de assessments"
    info "   ✓ Portal do cliente com dashboard"
    info "   ✓ Suporte timezone Brasil (GMT-3)"
    info "   ✓ Relatórios PDF formais e profissionais"
    info "   ✓ Gestão avançada de perguntas com drag-and-drop"
    info "   ✓ Sistema de criptografia e segurança aprimorado"
    
    echo ""
    info "📋 COMANDOS ÚTEIS:"
    info "   sudo tail -f /var/log/supervisor/assessment.log"
    info "   sudo supervisorctl status assessment"
    info "   sudo supervisorctl restart assessment"
    info "   sudo systemctl status nginx"
    
    echo ""
    local IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
    log "🌍 Aplicação disponível em: http://$IP"
    
    echo ""
    info "🧪 PARA TESTAR AS NOVAS FUNCIONALIDADES:"
    info "   1. Acesse o admin e crie um assessment"
    info "   2. Adicione domínios e perguntas"
    info "   3. Crie um projeto e respondentes"
    info "   4. Complete uma avaliação"
    info "   5. Gere relatório PDF para ver o gráfico radar"
    
    log "🎉 SISTEMA PRONTO PARA USO!"
}

# Função principal
main() {
    log "🚀 Iniciando deploy Sistema de Avaliações v2.0..."
    
    check_dependencies
    backup_current
    reset_and_deploy
    setup_python_env
    initialize_database
    setup_permissions
    restart_services
    health_check
    post_deploy_info
}

# Executar
main "$@"