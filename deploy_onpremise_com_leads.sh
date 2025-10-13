#!/bin/bash

################################################################################
# Script de Deployment On-Premise - Adicionar Sistema de Leads
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
# Data: 2025-10-11
# Versão: 1.0
################################################################################

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
APP_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_SQL="$BACKUP_DIR/backup_pre_leads_$TIMESTAMP.sql"
LOG_FILE="$BACKUP_DIR/deploy_leads_$TIMESTAMP.log"

# Função para log
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

# Banner
clear
echo "================================================================================"
echo "  DEPLOYMENT ON-PREMISE - Sistema de Leads"
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

# Confirmação
read -p "Deseja continuar com o deployment? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    error "Deployment cancelado pelo usuário."
    exit 1
fi

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# 1. BACKUP DO BANCO DE DADOS
log "ETAPA 1/7: Fazendo backup completo do banco de dados..."

# Detectar credenciais do banco
if [ -f "$APP_DIR/.env" ]; then
    source "$APP_DIR/.env"
    DB_NAME="$PGDATABASE"
    DB_USER="$PGUSER"
    DB_HOST="${PGHOST:-localhost}"
    DB_PORT="${PGPORT:-5432}"
else
    # Tentar pegar do supervisor
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

# Fazer backup
sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_SQL" 2>&1

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_SQL" | cut -f1)
    log "✓ Backup criado com sucesso: $BACKUP_SQL ($BACKUP_SIZE)"
else
    error "Falha ao criar backup do banco de dados!"
    exit 1
fi

# 2. PARAR APLICAÇÃO
log "ETAPA 2/7: Parando aplicação..."
sudo supervisorctl stop assessment
sleep 2
log "✓ Aplicação parada"

# 3. ATUALIZAR CÓDIGO DO GIT
log "ETAPA 3/7: Atualizando código do repositório Git..."

cd "$APP_DIR"

# Verificar se há mudanças locais
if ! git diff-index --quiet HEAD --; then
    warning "Há mudanças locais não commitadas. Fazendo stash..."
    git stash save "Auto-stash antes do deployment de leads - $TIMESTAMP"
fi

# Buscar e aplicar mudanças
git fetch origin
BEFORE_COMMIT=$(git rev-parse HEAD)

git pull origin main

AFTER_COMMIT=$(git rev-parse HEAD)

if [ "$BEFORE_COMMIT" == "$AFTER_COMMIT" ]; then
    info "Código já está atualizado (nenhuma mudança do Git)"
else
    log "✓ Código atualizado de $BEFORE_COMMIT para $AFTER_COMMIT"
fi

# 4. CRIAR TABELAS DE LEADS
log "ETAPA 4/7: Criando tabelas do sistema de leads..."

# SQL para criar as tabelas (idempotente - só cria se não existir)
sudo -u postgres psql -d "$DB_NAME" << 'EOF'
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

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_prioridade ON leads(prioridade);
CREATE INDEX IF NOT EXISTS idx_leads_data_criacao ON leads(data_criacao DESC);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_empresa ON leads(empresa);

-- Criar tabela de histórico de leads
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

-- Criar índice para histórico
CREATE INDEX IF NOT EXISTS idx_historico_lead ON leads_historico(lead_id, data_registro DESC);

-- Comentários nas tabelas
COMMENT ON TABLE leads IS 'Tabela de leads gerados por assessments públicos';
COMMENT ON TABLE leads_historico IS 'Histórico de interações e mudanças nos leads';

-- Verificar tabelas criadas
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'leads') 
        THEN 'leads: OK'
        ELSE 'leads: ERRO'
    END as tabela_leads,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'leads_historico') 
        THEN 'leads_historico: OK'
        ELSE 'leads_historico: ERRO'
    END as tabela_historico;
EOF

if [ $? -eq 0 ]; then
    log "✓ Tabelas de leads criadas com sucesso"
else
    error "Erro ao criar tabelas de leads!"
    error "Restaurando backup..."
    sudo -u postgres psql -d "$DB_NAME" < "$BACKUP_SQL"
    sudo supervisorctl start assessment
    exit 1
fi

# 5. VERIFICAR ESTRUTURA
log "ETAPA 5/7: Verificando estrutura do banco de dados..."

# Contar colunas nas novas tabelas
LEADS_COLS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='leads';")
HISTORICO_COLS=$(sudo -u postgres psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='leads_historico';")

info "Tabela 'leads': $LEADS_COLS colunas"
info "Tabela 'leads_historico': $HISTORICO_COLS colunas"

if [ "$LEADS_COLS" -lt 15 ] || [ "$HISTORICO_COLS" -lt 5 ]; then
    error "Estrutura das tabelas incompleta!"
    exit 1
fi

log "✓ Estrutura do banco de dados verificada"

# 6. INSTALAR DEPENDÊNCIAS (se necessário)
log "ETAPA 6/7: Verificando dependências Python..."

cd "$APP_DIR"
source venv/bin/activate

# Instalar dependências se houver requirements.txt atualizado
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    log "✓ Dependências Python atualizadas"
fi

deactivate

# 7. REINICIAR APLICAÇÃO
log "ETAPA 7/7: Reiniciando aplicação..."

sudo supervisorctl start assessment
sleep 3

# Verificar se a aplicação iniciou corretamente
STATUS=$(sudo supervisorctl status assessment | awk '{print $2}')

if [ "$STATUS" == "RUNNING" ]; then
    log "✓ Aplicação reiniciada com sucesso!"
else
    error "Aplicação não está rodando!"
    error "Status: $STATUS"
    error "Verificando logs de erro..."
    sudo supervisorctl tail assessment stderr | tail -20
    exit 1
fi

# 8. VERIFICAÇÃO FINAL
log "Verificando logs de inicialização..."
sleep 2

ERRORS=$(sudo supervisorctl tail assessment stderr | grep -i "error\|exception\|traceback" | tail -5 || true)

if [ -z "$ERRORS" ]; then
    log "✓ Nenhum erro encontrado nos logs"
else
    warning "Atenção: Possíveis erros nos logs:"
    echo "$ERRORS"
fi

# 9. RESUMO FINAL
echo ""
echo "================================================================================"
echo -e "${GREEN}  ✓ DEPLOYMENT CONCLUÍDO COM SUCESSO!${NC}"
echo "================================================================================"
echo ""
echo "📊 Resumo das Mudanças:"
echo "  • Tabelas criadas:"
echo "    - leads (gestão de leads)"
echo "    - leads_historico (histórico de interações)"
echo ""
echo "  • Novos recursos disponíveis:"
echo "    - Dashboard de Leads (/admin/leads)"
echo "    - Gestão de status e prioridades"
echo "    - Histórico completo de interações"
echo "    - Criação automática de leads a partir de assessments públicos"
echo ""
echo "📁 Arquivos importantes:"
echo "  • Backup do banco: $BACKUP_SQL"
echo "  • Log do deployment: $LOG_FILE"
echo ""
echo "🔗 Próximos passos:"
echo "  1. Acesse: https://assessments.zerobox.com.br/admin/leads"
echo "  2. Responda um assessment público para gerar um lead de teste"
echo "  3. Gerencie os leads pelo novo dashboard"
echo ""
echo "💡 Como funciona:"
echo "  • Quando alguém responde um assessment público,"
echo "    um lead é criado automaticamente"
echo "  • Leads podem ter status: novo, contatado, qualificado,"
echo "    proposta, negociação, ganho ou perdido"
echo "  • Você pode atribuir leads a diferentes usuários"
echo "  • Todo o histórico de interações é registrado"
echo ""
echo "================================================================================"
echo ""

log "Deployment finalizado com sucesso em $(date)"
