#!/bin/bash

# Script de Deploy para Servidor Ubuntu
# Sistema de Avaliações de Maturidade
# Gruppen Serviços de Informática Ltda

set -e  # Para em caso de erro

echo "=========================================="
echo "Deploy - Sistema de Avaliações de Maturidade"
echo "=========================================="

# Configurações
APP_NAME="assessment"
APP_DIR="/var/www/$APP_NAME"
REPO_URL="https://github.com/seuusuario/assessment-system.git"  # Substitua pela URL do seu repo
BACKUP_DIR="/var/backups/$APP_NAME"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar se está rodando como root
if [[ $EUID -eq 0 ]]; then
   error "Este script não deve ser executado como root"
   exit 1
fi

# Verificar dependências
check_dependencies() {
    log "Verificando dependências..."
    
    if ! command -v git &> /dev/null; then
        error "Git não está instalado"
        exit 1
    fi
    
    if ! command -v python3.11 &> /dev/null; then
        error "Python 3.11 não está instalado"
        exit 1
    fi
    
    if ! command -v supervisorctl &> /dev/null; then
        error "Supervisor não está instalado"
        exit 1
    fi
    
    log "Dependências verificadas com sucesso"
}

# Criar backup
create_backup() {
    if [ -d "$APP_DIR" ]; then
        log "Criando backup da aplicação atual..."
        sudo mkdir -p "$BACKUP_DIR"
        BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        sudo tar -czf "$BACKUP_FILE" -C "$APP_DIR" .
        log "Backup criado: $BACKUP_FILE"
    fi
}

# Deploy da aplicação
deploy_app() {
    log "Iniciando deploy da aplicação..."
    
    # Parar a aplicação
    log "Parando aplicação..."
    sudo supervisorctl stop $APP_NAME || true
    
    # Criar diretório se não existir
    sudo mkdir -p "$APP_DIR"
    sudo chown $USER:$USER "$APP_DIR"
    
    # Clone ou pull do repositório
    if [ -d "$APP_DIR/.git" ]; then
        log "Atualizando código existente..."
        cd "$APP_DIR"
        git fetch origin
        git reset --hard origin/main
    else
        log "Clonando repositório..."
        git clone "$REPO_URL" "$APP_DIR"
        cd "$APP_DIR"
    fi
    
    # Configurar ambiente virtual
    log "Configurando ambiente virtual..."
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Configurar permissões
    log "Configurando permissões..."
    sudo chown -R www-data:www-data "$APP_DIR"
    sudo chmod -R 755 "$APP_DIR"
    
    # Migrar banco de dados
    log "Executando migrações do banco..."
    source venv/bin/activate
    python init_db.py
    
    # Reiniciar serviços
    log "Reiniciando serviços..."
    sudo supervisorctl start $APP_NAME
    sudo systemctl reload nginx
    
    log "Deploy concluído com sucesso!"
}

# Verificar status dos serviços
check_status() {
    log "Verificando status dos serviços..."
    
    echo "Status do Supervisor:"
    sudo supervisorctl status $APP_NAME
    
    echo ""
    echo "Status do Nginx:"
    sudo systemctl status nginx --no-pager -l
    
    echo ""
    echo "Últimas linhas do log:"
    sudo tail -n 20 /var/log/$APP_NAME.log
}

# Menu principal
case "${1:-}" in
    "install")
        check_dependencies
        create_backup
        deploy_app
        check_status
        ;;
    "update")
        create_backup
        deploy_app
        check_status
        ;;
    "status")
        check_status
        ;;
    "backup")
        create_backup
        ;;
    *)
        echo "Uso: $0 {install|update|status|backup}"
        echo ""
        echo "  install - Primeira instalação"
        echo "  update  - Atualizar aplicação existente"
        echo "  status  - Verificar status dos serviços"
        echo "  backup  - Criar backup manual"
        exit 1
        ;;
esac