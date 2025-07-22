#!/bin/bash

# Script de atualização do Sistema de Avaliações de Maturidade
# Atualiza código, dependências e reinicia serviços

set -e  # Parar em caso de erro

# Configurações
APP_DIR="/var/www/assessment"
BACKUP_DIR="/var/backups/assessment"
LOG_FILE="/var/log/assessment_update.log"
USER="www-data"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Função para exibir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "INFO: $1"
}

print_success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
    log "SUCESSO: $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
    log "AVISO: $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
    log "ERRO: $1"
}

# Verificar se está executando como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Este script deve ser executado como root"
        exit 1
    fi
}

# Criar backup do sistema atual
create_backup() {
    print_status "Criando backup do sistema atual..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    # Criar diretório de backup
    mkdir -p "$BACKUP_DIR"
    
    # Backup do código
    print_status "Fazendo backup do código..."
    tar -czf "$BACKUP_PATH/codigo.tar.gz" -C "$APP_DIR" . \
        --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='venv'
    
    # Backup do banco de dados
    print_status "Fazendo backup do banco de dados..."
    if [[ -f "$APP_DIR/.env" ]]; then
        source "$APP_DIR/.env"
        if [[ -n "$DATABASE_URL" ]]; then
            # Extrair dados da URL do PostgreSQL
            DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
            DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
            
            export PGPASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
            pg_dump -h localhost -U "$DB_USER" "$DB_NAME" > "$BACKUP_PATH/database.sql"
            unset PGPASSWORD
            
            print_success "Backup do banco criado"
        else
            print_warning "DATABASE_URL não encontrada no .env"
        fi
    else
        print_warning "Arquivo .env não encontrado"
    fi
    
    # Backup das configurações
    print_status "Fazendo backup das configurações..."
    mkdir -p "$BACKUP_PATH/config"
    
    if [[ -f "/etc/supervisor/conf.d/assessment.conf" ]]; then
        cp "/etc/supervisor/conf.d/assessment.conf" "$BACKUP_PATH/config/"
    fi
    
    if [[ -f "/etc/nginx/sites-available/assessment" ]]; then
        cp "/etc/nginx/sites-available/assessment" "$BACKUP_PATH/config/"
    fi
    
    print_success "Backup criado em: $BACKUP_PATH"
    echo "$BACKUP_PATH" > /tmp/last_backup_path
}

# Atualizar código do repositório
update_code() {
    print_status "Atualizando código do repositório..."
    
    cd "$APP_DIR"
    
    # Verificar se é um repositório git
    if [[ -d ".git" ]]; then
        # Salvar mudanças locais se existirem
        if ! git diff --quiet; then
            print_warning "Mudanças locais detectadas, criando stash..."
            sudo -u "$USER" git stash
        fi
        
        # Atualizar do repositório remoto
        sudo -u "$USER" git fetch origin
        sudo -u "$USER" git pull origin main
        
        print_success "Código atualizado do repositório"
    else
        print_warning "Diretório não é um repositório git, pulando atualização de código"
    fi
}

# Atualizar dependências Python
update_dependencies() {
    print_status "Atualizando dependências Python..."
    
    cd "$APP_DIR"
    
    if [[ -f "requirements.txt" ]]; then
        sudo -u "$USER" venv/bin/pip install --upgrade pip
        sudo -u "$USER" venv/bin/pip install -r requirements.txt --upgrade
        print_success "Dependências Python atualizadas"
    else
        print_warning "requirements.txt não encontrado"
    fi
}

# Executar migrações do banco
run_migrations() {
    print_status "Executando migrações do banco de dados..."
    
    cd "$APP_DIR"
    
    # Verificar se existe script de migração
    if [[ -f "migrar_banco.py" ]]; then
        sudo -u "$USER" bash -c "source venv/bin/activate && python migrar_banco.py"
        print_success "Migrações executadas"
    else
        print_status "Criando/atualizando tabelas..."
        sudo -u "$USER" bash -c "source venv/bin/activate && python -c \"
from app import create_app, db
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
    db.create_all()
print('Tabelas atualizadas')
\""
        print_success "Estrutura do banco atualizada"
    fi
}

# Reiniciar serviços
restart_services() {
    print_status "Reiniciando serviços..."
    
    # Reiniciar aplicação
    if systemctl is-active --quiet supervisor; then
        supervisorctl reread
        supervisorctl update
        supervisorctl restart assessment
        print_success "Aplicação reiniciada via supervisor"
    else
        print_error "Supervisor não está ativo"
        return 1
    fi
    
    # Reiniciar nginx se necessário
    if systemctl is-active --quiet nginx; then
        nginx -t && systemctl reload nginx
        print_success "Nginx recarregado"
    else
        print_warning "Nginx não está ativo"
    fi
}

# Verificar se atualização funcionou
verify_update() {
    print_status "Verificando se atualização funcionou..."
    
    cd "$APP_DIR"
    
    # Aguardar aplicação inicializar
    sleep 10
    
    # Verificar se processo está rodando
    if supervisorctl status assessment | grep -q "RUNNING"; then
        print_success "Aplicação está rodando"
    else
        print_error "Aplicação não está rodando"
        return 1
    fi
    
    # Testar conectividade HTTP local
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302\|403"; then
        print_success "Aplicação respondendo a requisições HTTP"
    else
        print_warning "Aplicação pode não estar respondendo corretamente"
    fi
    
    # Executar verificação completa se script existir
    if [[ -f "verificar_instalacao.py" ]]; then
        print_status "Executando verificação completa..."
        if sudo -u "$USER" bash -c "source venv/bin/activate && python verificar_instalacao.py" >> "$LOG_FILE" 2>&1; then
            print_success "Verificação completa passou"
        else
            print_warning "Verificação completa encontrou problemas (veja $LOG_FILE)"
        fi
    fi
    
    return 0
}

# Função de rollback em caso de falha
rollback() {
    print_error "Atualização falhou, executando rollback..."
    
    if [[ -f "/tmp/last_backup_path" ]]; then
        BACKUP_PATH=$(cat /tmp/last_backup_path)
        
        if [[ -f "$BACKUP_PATH/codigo.tar.gz" ]]; then
            print_status "Restaurando código..."
            cd "$APP_DIR"
            rm -rf * .[^.]*  # Remove tudo exceto .. e .
            tar -xzf "$BACKUP_PATH/codigo.tar.gz" -C .
            chown -R "$USER:$USER" .
        fi
        
        if [[ -f "$BACKUP_PATH/database.sql" ]]; then
            print_status "Restaurando banco de dados..."
            source "$APP_DIR/.env"
            DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
            DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
            
            export PGPASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
            psql -h localhost -U "$DB_USER" "$DB_NAME" < "$BACKUP_PATH/database.sql"
            unset PGPASSWORD
        fi
        
        # Reiniciar serviços após rollback
        restart_services
        
        print_success "Rollback concluído"
    else
        print_error "Não foi possível localizar backup para rollback"
    fi
}

# Função principal
main() {
    echo "========================================================"
    echo "🔄 ATUALIZAÇÃO DO SISTEMA DE AVALIAÇÕES DE MATURIDADE"
    echo "========================================================"
    echo "📅 $(date '+%d/%m/%Y %H:%M:%S')"
    echo ""
    
    # Verificar se é root
    check_root
    
    # Verificar se diretório da aplicação existe
    if [[ ! -d "$APP_DIR" ]]; then
        print_error "Diretório da aplicação não encontrado: $APP_DIR"
        exit 1
    fi
    
    # Criar log de atualização
    log "=== INÍCIO DA ATUALIZAÇÃO ==="
    
    # Executar passos da atualização
    create_backup || {
        print_error "Falha ao criar backup"
        exit 1
    }
    
    update_code || {
        print_error "Falha ao atualizar código"
        rollback
        exit 1
    }
    
    update_dependencies || {
        print_error "Falha ao atualizar dependências"
        rollback
        exit 1
    }
    
    run_migrations || {
        print_error "Falha ao executar migrações"
        rollback
        exit 1
    }
    
    restart_services || {
        print_error "Falha ao reiniciar serviços"
        rollback
        exit 1
    }
    
    verify_update || {
        print_error "Verificação pós-atualização falhou"
        rollback
        exit 1
    }
    
    log "=== ATUALIZAÇÃO CONCLUÍDA COM SUCESSO ==="
    
    echo ""
    echo "========================================================"
    echo "🎉 ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "========================================================"
    echo "📊 Sistema atualizado e funcionando"
    echo "📝 Log disponível em: $LOG_FILE"
    echo "💾 Backup disponível em: $(cat /tmp/last_backup_path 2>/dev/null || echo 'N/A')"
    echo "========================================================"
}

# Executar função principal
main "$@"