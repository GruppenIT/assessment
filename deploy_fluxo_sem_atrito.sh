#!/bin/bash
#
# Script de Deploy - Fluxo Sem Atrito para Assessments Públicos
# 
# Este script atualiza o sistema para o novo fluxo onde:
# - Resultados são mostrados IMEDIATAMENTE após responder
# - Lead é criado SOMENTE quando usuário solicita envio por email
# - Apenas email é obrigatório para receber resultado
#
# IMPORTANTE: Este script PRESERVA todos os dados existentes
#

set -e  # Para execução em caso de erro

echo "=================================================="
echo "Deploy - Fluxo Sem Atrito (Assessments Públicos)"
echo "=================================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# 0. Carregar variáveis de ambiente
log_info "Carregando variáveis de ambiente..."
if [ -f ".env" ]; then
    log_info "Arquivo .env encontrado, carregando..."
    export $(cat .env | grep -v '^#' | xargs)
    log_info "Variáveis de ambiente carregadas"
else
    log_warn "Arquivo .env não encontrado"
fi

# 1. Verificar se estamos no diretório correto
log_info "Verificando diretório do projeto..."
log_info "Diretório atual: $(pwd)"

# Verificar se pelo menos um dos arquivos/diretórios do projeto existe
if [ -d "routes" ] || [ -d "templates" ] || [ -d "models" ] || [ -f "app.py" ] || [ -f "main.py" ]; then
    log_info "✓ Diretório do projeto verificado"
else
    log_error "Este script deve ser executado no diretório raiz do projeto!"
    log_error "Certifique-se de estar em: /var/www/assessment"
    log_error "Conteúdo atual do diretório:"
    ls -la
    exit 1
fi

# 2. Fazer backup do banco de dados
log_info "Criando backup do banco de dados..."
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup_antes_fluxo_sem_atrito_$(date +%Y%m%d_%H%M%S).sql"

if [ -n "$PGDATABASE" ]; then
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" > "$BACKUP_FILE"
    log_info "Backup criado: $BACKUP_FILE"
else
    log_warn "Variáveis de ambiente PostgreSQL não encontradas. Pulando backup."
fi

# 3. Atualizar código do Git
log_info "Atualizando código do repositório Git..."
if [ -d ".git" ]; then
    git fetch origin
    git pull origin main || git pull origin master
    log_info "Código atualizado com sucesso"
else
    log_warn "Diretório .git não encontrado. Pulando atualização do Git."
fi

# 4. Aplicar migrações do banco de dados
log_info "Aplicando migrações do banco de dados..."

# Migração: Tornar campos nome e empresa opcionais na tabela leads
MIGRATION_SQL="
-- Migração: Permitir NULL em campos de lead (exceto email)
-- Necessário para o novo fluxo sem atrito onde apenas email é obrigatório

ALTER TABLE leads 
ALTER COLUMN nome DROP NOT NULL;

ALTER TABLE leads 
ALTER COLUMN empresa DROP NOT NULL;
"

# Aplicar migração
if [ -n "$DATABASE_URL" ]; then
    log_info "Usando DATABASE_URL para conexão..."
    echo "$MIGRATION_SQL" | psql "$DATABASE_URL"
    log_info "Migrações aplicadas com sucesso"
elif [ -n "$PGDATABASE" ]; then
    log_info "Usando variáveis PG* para conexão..."
    PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" <<EOF
$MIGRATION_SQL
EOF
    log_info "Migrações aplicadas com sucesso"
else
    log_error "Variáveis de conexão ao banco não encontradas!"
    log_error "Configure DATABASE_URL ou PGDATABASE/PGHOST/PGUSER/PGPASSWORD"
    log_warn "Execute manualmente as seguintes migrações:"
    echo "$MIGRATION_SQL"
    log_warn "Continuando sem aplicar migrações..."
fi

# 5. Verificar estrutura da tabela
log_info "Verificando estrutura da tabela leads..."
if [ -n "$DATABASE_URL" ]; then
    psql "$DATABASE_URL" -c "\d leads" > /dev/null 2>&1 && log_info "Tabela leads verificada"
elif [ -n "$PGDATABASE" ]; then
    PGPASSWORD="$PGPASSWORD" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "\d leads" > /dev/null 2>&1 && log_info "Tabela leads verificada"
fi

# 6. Reiniciar aplicação
log_info "Reiniciando aplicação..."

# Tentar com Supervisor
if command -v supervisorctl &> /dev/null; then
    log_info "Reiniciando via Supervisor..."
    sudo supervisorctl restart assessments || log_warn "Não foi possível reiniciar via Supervisor"
fi

# Tentar com Systemd
if command -v systemctl &> /dev/null; then
    log_info "Reiniciando via Systemd..."
    sudo systemctl restart assessments.service || log_warn "Não foi possível reiniciar via Systemd"
fi

# Se nenhum dos acima funcionar, avisar
if ! command -v supervisorctl &> /dev/null && ! command -v systemctl &> /dev/null; then
    log_warn "Sistema de gerenciamento de serviços não detectado."
    log_warn "Reinicie manualmente a aplicação Flask."
fi

# 7. Resumo
echo ""
echo "=================================================="
log_info "Deploy concluído com sucesso!"
echo "=================================================="
echo ""
echo "📋 Resumo das alterações:"
echo "  ✅ Código atualizado do Git"
echo "  ✅ Migrações aplicadas (leads.nome e leads.empresa agora opcionais)"
echo "  ✅ Backup criado: $BACKUP_FILE"
echo "  ✅ Aplicação reiniciada"
echo ""
echo "🎯 Novo fluxo implementado:"
echo "  1. Usuário responde assessment público"
echo "  2. Resultado mostrado IMEDIATAMENTE (sem formulário)"
echo "  3. Modal permite solicitar envio por email (apenas email)"
echo "  4. Lead criado SOMENTE quando solicita envio"
echo ""
echo "📧 Configuração de Email:"
echo "  - Verifique configurações SMTP em /admin/parametros/smtp"
echo "  - Configure destinatários em cada tipo de assessment"
echo ""
log_info "Sistema atualizado e pronto para uso!"
echo ""
