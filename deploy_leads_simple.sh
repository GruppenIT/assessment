#!/bin/bash
# Deploy Sistema de Leads - Versao Simples
# Sem cores, sem caracteres especiais

set -e

APP_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_SQL="$BACKUP_DIR/backup_pre_leads_$TIMESTAMP.sql"
LOG_FILE="$BACKUP_DIR/deploy_leads_$TIMESTAMP.log"

log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_msg() {
    echo "[ERRO] $1" | tee -a "$LOG_FILE"
}

info_msg() {
    echo "[INFO] $1" | tee -a "$LOG_FILE"
}

clear
echo "========================================================================"
echo "  DEPLOYMENT ON-PREMISE - Sistema de Leads"
echo "========================================================================"
echo ""
echo "  Este script ira:"
echo "  - Fazer backup completo do banco de dados"
echo "  - Atualizar o codigo da aplicacao"
echo "  - Criar tabelas: leads e leads_historico"
echo "  - Preservar TODOS os dados existentes"
echo ""
echo "  Diretorio: $APP_DIR"
echo "  Backup em: $BACKUP_DIR"
echo ""
echo "========================================================================"
echo ""

read -p "Deseja continuar com o deployment? (s/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    error_msg "Deployment cancelado pelo usuario."
    exit 1
fi

mkdir -p "$BACKUP_DIR"

log_msg "ETAPA 1/7: Fazendo backup completo do banco de dados..."

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
    error_msg "Nao foi possivel detectar as credenciais do banco de dados!"
    exit 1
fi

info_msg "Banco de dados: $DB_NAME"
info_msg "Usuario: $DB_USER"

sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_SQL" 2>&1

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_SQL" | cut -f1)
    log_msg "Backup criado com sucesso: $BACKUP_SQL ($BACKUP_SIZE)"
else
    error_msg "Falha ao criar backup do banco de dados!"
    exit 1
fi

log_msg "ETAPA 2/7: Parando aplicacao..."
sudo supervisorctl stop assessment
sleep 2
log_msg "Aplicacao parada"

log_msg "ETAPA 3/7: Atualizando codigo do repositorio Git..."

cd "$APP_DIR"

if ! git diff-index --quiet HEAD --; then
    info_msg "Ha mudancas locais nao commitadas. Fazendo stash..."
    git stash save "Auto-stash antes do deployment de leads - $TIMESTAMP"
fi

git fetch origin
BEFORE_COMMIT=$(git rev-parse HEAD)
git pull origin main
AFTER_COMMIT=$(git rev-parse HEAD)

if [ "$BEFORE_COMMIT" == "$AFTER_COMMIT" ]; then
    info_msg "Codigo ja esta atualizado"
else
    log_msg "Codigo atualizado: $BEFORE_COMMIT -> $AFTER_COMMIT"
fi

log_msg "ETAPA 4/7: Criando tabelas do sistema de leads..."

sudo -u postgres psql -d "$DB_NAME" << 'EOSQL'
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

COMMENT ON TABLE leads IS 'Tabela de leads gerados por assessments publicos';
COMMENT ON TABLE leads_historico IS 'Historico de interacoes e mudancas nos leads';
EOSQL

if [ $? -eq 0 ]; then
    log_msg "Tabelas de leads criadas com sucesso"
else
    error_msg "Erro ao criar tabelas de leads!"
    error_msg "Restaurando backup..."
    sudo -u postgres psql -d "$DB_NAME" < "$BACKUP_SQL"
    sudo supervisorctl start assessment
    exit 1
fi

log_msg "ETAPA 5/7: Verificando estrutura do banco de dados..."

LEADS_COLS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='leads';")
HISTORICO_COLS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='leads_historico';")

info_msg "Tabela 'leads': $LEADS_COLS colunas"
info_msg "Tabela 'leads_historico': $HISTORICO_COLS colunas"

if [ "$LEADS_COLS" -lt 15 ] || [ "$HISTORICO_COLS" -lt 5 ]; then
    error_msg "Estrutura das tabelas incompleta!"
    exit 1
fi

log_msg "Estrutura do banco de dados verificada"

log_msg "ETAPA 6/7: Verificando dependencias Python..."

cd "$APP_DIR"
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    log_msg "Dependencias Python atualizadas"
fi

deactivate

log_msg "ETAPA 7/7: Reiniciando aplicacao..."

sudo supervisorctl start assessment
sleep 3

STATUS=$(sudo supervisorctl status assessment | awk '{print $2}')

if [ "$STATUS" == "RUNNING" ]; then
    log_msg "Aplicacao reiniciada com sucesso!"
else
    error_msg "Aplicacao nao esta rodando!"
    error_msg "Status: $STATUS"
    sudo supervisorctl tail assessment stderr | tail -20
    exit 1
fi

log_msg "Verificando logs de inicializacao..."
sleep 2

ERRORS=$(sudo supervisorctl tail assessment stderr | grep -i "error\|exception\|traceback" | tail -5 || true)

if [ -z "$ERRORS" ]; then
    log_msg "Nenhum erro encontrado nos logs"
else
    echo "Atencao: Possiveis erros nos logs:"
    echo "$ERRORS"
fi

echo ""
echo "========================================================================"
echo "  DEPLOYMENT CONCLUIDO COM SUCESSO!"
echo "========================================================================"
echo ""
echo "Resumo das Mudancas:"
echo "  - Tabelas criadas: leads, leads_historico"
echo "  - Dashboard de Leads: /admin/leads"
echo ""
echo "Arquivos:"
echo "  - Backup: $BACKUP_SQL"
echo "  - Log: $LOG_FILE"
echo ""
echo "Acesse: https://assessments.zerobox.com.br/admin/leads"
echo ""
echo "========================================================================"
echo ""

log_msg "Deployment finalizado com sucesso em $(date)"
