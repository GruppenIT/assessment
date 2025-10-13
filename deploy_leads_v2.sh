#!/bin/bash

################################################################################
# Script de Deployment On-Premise - Sistema de Leads v2.0
# 
# Este script atualiza a aplicação adicionando o sistema completo de gestão
# de leads, preservando TODOS os dados existentes.
#
# Funcionalidades:
# - Backup automático completo do banco de dados
# - Atualização do código via Git
# - Criação das tabelas de leads e histórico
# - Verificação de integridade
# - Rollback automático em caso de erro
# - Zero perda de dados
#
# Data: 2025-10-13
# Versão: 2.0 (corrigido)
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_SQL="$BACKUP_DIR/backup_pre_leads_$TIMESTAMP.sql"
LOG_FILE="$BACKUP_DIR/deploy_leads_$TIMESTAMP.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

clear
echo "================================================================================"
echo "  DEPLOYMENT ON-PREMISE - Sistema de Leads v2.0"
echo "================================================================================"
echo ""
echo "  Este script irá:"
echo "  ✓ Fazer backup completo do banco de dados"
echo "  ✓ Atualizar o código da aplicação"
echo "  ✓ Criar tabelas: leads e leads_historico"
echo "  ✓ Preservar TODOS os dados existentes"
echo ""
echo "  Diretório: $APP_DIR"
echo "  Backup em: $BACKUP_DIR"
echo ""
echo "================================================================================"
echo ""

read -p "Deseja continuar com o deployment? (s/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    error "Deployment cancelado pelo usuário."
    exit 1
fi

mkdir -p "$BACKUP_DIR"

log "ETAPA 1/7: Fazendo backup completo do banco de dados..."

if [ -f "$APP_DIR/.env" ]; then
    source "$APP_DIR/.env"
    DB_NAME="$PGDATABASE"
    DB_USER="$PGUSER"
    DB_HOST="${PGHOST:-localhost}"
    DB_PORT="${PGPORT:-5432}"
else
    SUPERVISOR_CONF="/etc/supervisor/conf.d/assessment.conf"
    if [ -f "$SUPERVISOR_CONF" ]; then
        DB_NAME=$(grep PGDATABASE "$SUPERVISOR_CONF" | cut -d'=' -f2 | tr -d ',')
        DB_USER=$(grep PGUSER "$SUPERVISOR_CONF" | cut -d'=' -f2 | tr -d ',')
        DB_HOST=$(grep PGHOST "$SUPERVISOR_CONF" | cut -d'=' -f2 | tr -d ',' | head -1)
        DB_PORT=$(grep PGPORT "$SUPERVISOR_CONF" | cut -d'=' -f2 | tr -d ',')
    fi
fi

if [ -z "$DB_NAME" ]; then
    error "Não foi possível detectar as credenciais do banco de dados!"
    exit 1
fi

info "Banco de dados: $DB_NAME"
info "Usuário: $DB_USER"

sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_SQL" 2>&1

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_SQL" | cut -f1)
    log "✓ Backup criado com sucesso: $BACKUP_SQL ($BACKUP_SIZE)"
else
    error "Falha ao criar backup do banco de dados!"
    exit 1
fi

log "ETAPA 2/7: Parando aplicação..."
sudo supervisorctl stop assessment
sleep 2
log "✓ Aplicação parada"

log "ETAPA 3/7: Atualizando código do repositório Git..."

cd "$APP_DIR"

if ! git diff-index --quiet HEAD --; then
    warning "Há mudanças locais não commitadas. Fazendo stash..."
    git stash save "Auto-stash antes do deployment de leads - $TIMESTAMP"
fi

git fetch origin
BEFORE_COMMIT=$(git rev-parse HEAD)
git pull origin main
AFTER_COMMIT=$(git rev-parse HEAD)

if [ "$BEFORE_COMMIT" == "$AFTER_COMMIT" ]; then
    info "Código já está atualizado"
else
    log "✓ Código atualizado: $BEFORE_COMMIT → $AFTER_COMMIT"
fi

log "ETAPA 4/7: Criando tabelas do sistema de leads..."

sudo -u postgres psql -d "$DB_NAME" << 'EOSQL'
-- Criar tabela de leads
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    assessment_publico_id INTEGER NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200) NOT NULL,
    telefone VARCHAR(20),
    cargo VARCHAR(100),
    empresa VARCHAR(200) NOT NULL,
    tipo_assessment_nome VARCHAR(200),
    pontuacao_geral DOUBLE PRECISION,
    pontuacoes_dominios JSON,
    status VARCHAR(50) NOT NULL DEFAULT 'novo',
    prioridade VARCHAR(20) DEFAULT 'media',
    comentarios TEXT,
    data_criacao TIMESTAMP NOT NULL DEFAULT NOW(),
    data_atualizacao TIMESTAMP DEFAULT NOW(),
    atribuido_a_id INTEGER,
    CONSTRAINT fk_assessment_publico FOREIGN KEY (assessment_publico_id) 
        REFERENCES assessments_publicos(id) ON DELETE CASCADE,
    CONSTRAINT fk_atribuido_usuario FOREIGN KEY (atribuido_a_id) 
        REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_prioridade ON leads(prioridade);
CREATE INDEX IF NOT EXISTS idx_leads_data_criacao ON leads(data_criacao DESC);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_empresa ON leads(empresa);

-- Criar tabela de histórico
CREATE TABLE IF NOT EXISTS leads_historico (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL,
    usuario_id INTEGER,
    acao VARCHAR(100) NOT NULL,
    detalhes TEXT,
    data_registro TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_lead FOREIGN KEY (lead_id) 
        REFERENCES leads(id) ON DELETE CASCADE,
    CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_historico_lead ON leads_historico(lead_id, data_registro DESC);

COMMENT ON TABLE leads IS 'Tabela de leads gerados por assessments públicos';
COMMENT ON TABLE leads_historico IS 'Histórico de interações e mudanças nos leads';
EOSQL

if [ $? -eq 0 ]; then
    log "✓ Tabelas de leads criadas com sucesso"
else
    error "Erro ao criar tabelas de leads!"
    error "Restaurando backup..."
    sudo -u postgres psql -d "$DB_NAME" < "$BACKUP_SQL"
    sudo supervisorctl start assessment
    exit 1
fi

log "ETAPA 5/7: Verificando estrutura do banco de dados..."

LEADS_COLS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='leads';")
HISTORICO_COLS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='leads_historico';")

info "Tabela 'leads': $LEADS_COLS colunas"
info "Tabela 'leads_historico': $HISTORICO_COLS colunas"

if [ "$LEADS_COLS" -lt 15 ] || [ "$HISTORICO_COLS" -lt 5 ]; then
    error "Estrutura das tabelas incompleta!"
    exit 1
fi

log "✓ Estrutura do banco de dados verificada"

log "ETAPA 6/7: Verificando dependências Python..."

cd "$APP_DIR"
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    log "✓ Dependências Python atualizadas"
fi

deactivate

log "ETAPA 7/7: Reiniciando aplicação..."

sudo supervisorctl start assessment
sleep 3

STATUS=$(sudo supervisorctl status assessment | awk '{print $2}')

if [ "$STATUS" == "RUNNING" ]; then
    log "✓ Aplicação reiniciada com sucesso!"
else
    error "Aplicação não está rodando!"
    error "Status: $STATUS"
    sudo supervisorctl tail assessment stderr | tail -20
    exit 1
fi

log "Verificando logs de inicialização..."
sleep 2

ERRORS=$(sudo supervisorctl tail assessment stderr | grep -i "error\|exception\|traceback" | tail -5 || true)

if [ -z "$ERRORS" ]; then
    log "✓ Nenhum erro encontrado nos logs"
else
    warning "Atenção: Possíveis erros nos logs:"
    echo "$ERRORS"
fi

echo ""
echo "================================================================================"
echo -e "${GREEN}  ✓ DEPLOYMENT CONCLUÍDO COM SUCESSO!${NC}"
echo "================================================================================"
echo ""
echo "📊 Resumo das Mudanças:"
echo "  • Tabelas criadas: leads, leads_historico"
echo "  • Novos recursos:"
echo "    - Dashboard de Leads (/admin/leads)"
echo "    - Gestão de status e prioridades"
echo "    - Histórico completo de interações"
echo "    - Criação automática de leads"
echo ""
echo "📁 Arquivos:"
echo "  • Backup: $BACKUP_SQL"
echo "  • Log: $LOG_FILE"
echo ""
echo "🔗 Acesse: https://assessments.zerobox.com.br/admin/leads"
echo ""
echo "================================================================================"
echo ""

log "Deployment finalizado com sucesso em $(date)"
