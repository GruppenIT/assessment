#!/bin/bash
# Sistema de Avaliações de Maturidade - Deploy On-Premise com Assessment Público
# Atualiza código do Git preservando dados existentes + aplica migração de Assessment Público

set -e  # Parar execução em caso de erro

echo "🚀 SISTEMA DE AVALIAÇÕES DE MATURIDADE - DEPLOY ON-PREMISE"
echo "========================================================="
echo "⚠️  ESTE SCRIPT PRESERVA TODOS OS DADOS EXISTENTES"
echo "   • Projetos, Clientes, Usuários e Assessments são mantidos"
echo "   • Backup completo é criado antes da atualização"
echo "   • Migração de Assessment Público será aplicada"
echo ""

# Verificar se está executando como root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script deve ser executado como root (sudo)"
   exit 1
fi

# Configurações
INSTALL_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment_backups"
GIT_REPO="https://github.com/GruppenIT/assessment.git"
SERVICE_NAME="assessment"
VENV_DIR="$INSTALL_DIR/venv"
LOG_FILE="/var/log/assessment_deploy.log"

# Função para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Função para backup completo
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$timestamp"
    
    log "📋 Criando backup completo..."
    mkdir -p "$backup_path"
    
    # Backup do código fonte
    if [ -d "$INSTALL_DIR" ]; then
        cp -r "$INSTALL_DIR" "$backup_path/code"
        log "   ✅ Código fonte copiado"
    fi
    
    # Backup do banco de dados PostgreSQL
    log "   💾 Fazendo backup do banco de dados..."
    if sudo -u postgres pg_dump assessment_db > "$backup_path/database_backup.sql" 2>/dev/null; then
        log "   ✅ Backup do banco criado: $backup_path/database_backup.sql"
    else
        log "   ⚠️  Não foi possível fazer backup do banco (pode não existir ainda)"
    fi
    
    # Backup da configuração do Supervisor
    if [ -f "/etc/supervisor/conf.d/assessment.conf" ]; then
        cp "/etc/supervisor/conf.d/assessment.conf" "$backup_path/"
        log "   ✅ Configuração Supervisor copiada"
    fi
    
    # Backup do arquivo .env se existir
    if [ -f "$INSTALL_DIR/.env" ]; then
        cp "$INSTALL_DIR/.env" "$backup_path/"
        log "   ✅ Arquivo .env copiado"
    fi
    
    echo "$backup_path" > /tmp/last_backup_path
    log "✅ Backup completo criado em: $backup_path"
}

# Função para verificar mudanças na estrutura do banco
check_database_changes() {
    log "🔍 Verificando mudanças na estrutura do banco..."
    
    local models_file="$INSTALL_DIR/models.py"
    local init_db_file="$INSTALL_DIR/init_db.py"
    
    if [ -f "$models_file" ]; then
        # Verificar por palavras-chave que indicam mudanças destrutivas
        if grep -q "db.drop_all\|DROP TABLE\|ALTER TABLE.*DROP" "$models_file" "$init_db_file" 2>/dev/null; then
            echo ""
            echo "🚨 ALERTA CRÍTICO: DETECTADAS OPERAÇÕES DESTRUTIVAS NO BANCO"
            echo "   • DROP TABLE, DROP COLUMN ou db.drop_all() encontrados"
            echo "   • Estas operações podem APAGAR DADOS EXISTENTES"
            echo ""
            read -p "⚠️  Deseja continuar mesmo assim? (digite 'SIM' para confirmar): " confirm
            if [ "$confirm" != "SIM" ]; then
                log "❌ Deploy cancelado pelo usuário devido a operações destrutivas"
                exit 1
            fi
        fi
    fi
}

# Função para parar serviços
stop_services() {
    log "🛑 Parando serviços..."
    if systemctl is-active --quiet supervisor; then
        supervisorctl stop "$SERVICE_NAME" 2>/dev/null || true
        log "   ✅ Serviço $SERVICE_NAME parado"
    fi
}

# Função para inicializar ou atualizar código
update_code() {
    log "📥 Atualizando código fonte..."
    
    if [ ! -d "$INSTALL_DIR/.git" ]; then
        log "   🌟 Primeira instalação - clonando repositório..."
        rm -rf "$INSTALL_DIR"
        git clone "$GIT_REPO" "$INSTALL_DIR"
    else
        log "   🔄 Atualizando código existente..."
        cd "$INSTALL_DIR"
        git fetch origin
        git reset --hard origin/main
    fi
    
    log "   ✅ Código atualizado"
}

# Função para configurar ambiente Python
setup_python_environment() {
    log "🐍 Configurando ambiente Python..."
    
    cd "$INSTALL_DIR"
    
    # Criar virtualenv se não existir
    if [ ! -d "$VENV_DIR" ]; then
        log "   🌟 Criando ambiente virtual..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Ativar virtualenv e instalar dependências
    source "$VENV_DIR/bin/activate"
    
    log "   📦 Instalando dependências..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log "   ✅ Ambiente Python configurado"
}

# Função para aplicar migração de Assessment Público
apply_public_assessment_migration() {
    log "🔄 Aplicando migração de Assessment Público..."
    
    cd "$INSTALL_DIR"
    
    # Verificar se o banco existe
    if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw assessment_db; then
        log "   ⚠️  Banco de dados não existe ainda, pulando migração"
        return 0
    fi
    
    # Criar arquivo SQL temporário com verificações idempotentes
    local migration_file="/tmp/public_assessment_migration_$$.sql"
    
    cat > "$migration_file" << 'EOF'
-- Migração Assessment Público - Idempotente (pode rodar múltiplas vezes)
-- Data: 2025-10-11

-- Adicionar coluna url_publica nas tabelas de tipos de assessment (se não existir)
-- Tabela antiga (tipos_assessment)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='tipos_assessment' AND column_name='url_publica'
    ) THEN
        ALTER TABLE tipos_assessment ADD COLUMN url_publica BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Coluna url_publica adicionada em tipos_assessment';
    ELSE
        RAISE NOTICE 'Coluna url_publica já existe em tipos_assessment';
    END IF;
END $$;

-- Tabela nova com versionamento (assessment_tipos)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='assessment_tipos' AND column_name='url_publica'
    ) THEN
        ALTER TABLE assessment_tipos ADD COLUMN url_publica BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Coluna url_publica adicionada em assessment_tipos';
    ELSE
        RAISE NOTICE 'Coluna url_publica já existe em assessment_tipos';
    END IF;
END $$;

-- Adicionar coluna telefone na tabela respondentes (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='respondentes' AND column_name='telefone'
    ) THEN
        ALTER TABLE respondentes ADD COLUMN telefone VARCHAR(20);
        RAISE NOTICE 'Coluna telefone adicionada em respondentes';
    ELSE
        RAISE NOTICE 'Coluna telefone já existe em respondentes';
    END IF;
END $$;

-- Adicionar coluna telefone na tabela clientes (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='clientes' AND column_name='telefone'
    ) THEN
        ALTER TABLE clientes ADD COLUMN telefone VARCHAR(20);
        RAISE NOTICE 'Coluna telefone adicionada em clientes';
    ELSE
        RAISE NOTICE 'Coluna telefone já existe em clientes';
    END IF;
END $$;

-- Criar tabela assessments_publicos (se não existir)
CREATE TABLE IF NOT EXISTS assessments_publicos (
    id SERIAL PRIMARY KEY,
    tipo_assessment_id INTEGER NOT NULL REFERENCES tipos_assessment(id),
    token VARCHAR(64) UNIQUE NOT NULL,
    
    -- Dados do respondente (opcionais até conclusão)
    nome_respondente VARCHAR(200),
    email_respondente VARCHAR(200),
    telefone_respondente VARCHAR(20),
    cargo_respondente VARCHAR(100),
    empresa_respondente VARCHAR(200),
    
    -- Controle
    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_conclusao TIMESTAMP,
    ip_address VARCHAR(50)
);

-- Criar índice no token (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename='assessments_publicos' AND indexname='idx_assessments_publicos_token'
    ) THEN
        CREATE INDEX idx_assessments_publicos_token ON assessments_publicos(token);
        RAISE NOTICE 'Índice idx_assessments_publicos_token criado';
    ELSE
        RAISE NOTICE 'Índice idx_assessments_publicos_token já existe';
    END IF;
END $$;

-- Criar tabela respostas_publicas (se não existir)
CREATE TABLE IF NOT EXISTS respostas_publicas (
    id SERIAL PRIMARY KEY,
    assessment_publico_id INTEGER NOT NULL REFERENCES assessments_publicos(id) ON DELETE CASCADE,
    pergunta_id INTEGER NOT NULL REFERENCES perguntas(id),
    valor INTEGER NOT NULL CHECK (valor IN (0, 3, 5)),
    data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_assessment_pergunta_publica UNIQUE (assessment_publico_id, pergunta_id)
);

-- Criar índices para performance (se não existirem)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename='respostas_publicas' AND indexname='idx_respostas_publicas_assessment'
    ) THEN
        CREATE INDEX idx_respostas_publicas_assessment ON respostas_publicas(assessment_publico_id);
        RAISE NOTICE 'Índice idx_respostas_publicas_assessment criado';
    ELSE
        RAISE NOTICE 'Índice idx_respostas_publicas_assessment já existe';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename='respostas_publicas' AND indexname='idx_respostas_publicas_pergunta'
    ) THEN
        CREATE INDEX idx_respostas_publicas_pergunta ON respostas_publicas(pergunta_id);
        RAISE NOTICE 'Índice idx_respostas_publicas_pergunta criado';
    ELSE
        RAISE NOTICE 'Índice idx_respostas_publicas_pergunta já existe';
    END IF;
END $$;

-- Adicionar comentários nas tabelas/colunas (sempre atualiza)
COMMENT ON TABLE assessments_publicos IS 'Armazena assessments respondidos publicamente sem autenticação';
COMMENT ON TABLE respostas_publicas IS 'Respostas individuais de assessments públicos';
COMMENT ON COLUMN assessments_publicos.token IS 'Token único para acessar o resultado do assessment';
COMMENT ON COLUMN respostas_publicas.valor IS 'Valor da resposta: 0=Não, 3=Parcial, 5=Sim';
EOF

    # Aplicar migração
    log "   📝 Executando migração SQL..."
    if sudo -u postgres psql -d assessment_db -f "$migration_file" 2>&1 | tee -a "$LOG_FILE"; then
        log "   ✅ Migração de Assessment Público aplicada com sucesso"
    else
        log "   ❌ Erro ao aplicar migração"
        rm -f "$migration_file"
        return 1
    fi
    
    # Remover arquivo temporário
    rm -f "$migration_file"
    
    # Verificar estrutura criada
    log "   🔍 Verificando tabelas criadas..."
    local tables=$(sudo -u postgres psql -d assessment_db -t -c "\dt assessments_publicos" 2>/dev/null | grep -c "assessments_publicos" || echo "0")
    if [ "$tables" -gt 0 ]; then
        log "   ✅ Tabela assessments_publicos confirmada"
    else
        log "   ⚠️  Tabela assessments_publicos não encontrada"
    fi
}

# Função para configurar banco de dados
setup_database() {
    log "💾 Configurando banco de dados..."
    
    cd "$INSTALL_DIR"
    
    # Verificar se PostgreSQL está rodando
    if ! systemctl is-active --quiet postgresql; then
        log "   🔄 Iniciando PostgreSQL..."
        systemctl start postgresql
    fi
    
    # Criar banco se não existir (preservando dados existentes)
    sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw assessment_db || {
        log "   🌟 Criando banco assessment_db..."
        sudo -u postgres createdb assessment_db
    }
    
    # Executar init_db.py apenas se for primeira instalação
    if [ -f "init_db.py" ]; then
        source "$VENV_DIR/bin/activate"
        
        # Verificar se já existem dados (tabela usuarios)
        if sudo -u postgres psql -d assessment_db -c "\dt" 2>/dev/null | grep -q "usuario\|users"; then
            log "   ℹ️  Banco de dados já contém dados, pulando inicialização"
        else
            log "   🔧 Inicializando estrutura do banco..."
            python3 init_db.py
        fi
    fi
    
    # Aplicar migração de Assessment Público
    apply_public_assessment_migration
    
    log "   ✅ Banco de dados configurado"
}

# Função para configurar Supervisor
setup_supervisor() {
    log "⚙️  Configurando Supervisor..."
    
    # Criar configuração do Supervisor
    cat > /etc/supervisor/conf.d/assessment.conf << EOF
[program:assessment]
directory=$INSTALL_DIR
command=$VENV_DIR/bin/gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 50 --reuse-port --reload wsgi:app
autostart=true
autorestart=true
stderr_logfile=/var/log/assessment_error.log
stdout_logfile=/var/log/assessment.log
user=www-data
environment=PATH="$VENV_DIR/bin"
EOF

    # Recarregar configuração do Supervisor
    supervisorctl reread
    supervisorctl update
    
    log "   ✅ Supervisor configurado"
}

# Função para definir permissões
set_permissions() {
    log "🔐 Configurando permissões..."
    
    chown -R www-data:www-data "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR"
    
    # Permissões especiais para diretórios sensíveis
    if [ -d "$INSTALL_DIR/uploads" ]; then
        chmod 750 "$INSTALL_DIR/uploads"
    fi
    
    log "   ✅ Permissões configuradas"
}

# Função para iniciar serviços
start_services() {
    log "🔄 Iniciando serviços..."
    
    systemctl enable supervisor
    systemctl start supervisor
    
    supervisorctl start "$SERVICE_NAME"
    sleep 3
    
    # Verificar se está rodando
    if supervisorctl status "$SERVICE_NAME" | grep -q "RUNNING"; then
        log "   ✅ Serviço $SERVICE_NAME iniciado com sucesso"
    else
        log "   ❌ Falha ao iniciar serviço, verificando logs..."
        supervisorctl tail "$SERVICE_NAME"
        return 1
    fi
}

# Função para verificar deploy
verify_deployment() {
    log "🔍 Verificando deployment..."
    
    # Aguardar alguns segundos para o serviço inicializar
    sleep 5
    
    # Testar se está respondendo
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/auth/login)
    
    if [ "$response_code" = "200" ]; then
        log "   ✅ Aplicação respondendo corretamente (código $response_code)"
    else
        log "   ⚠️  Aplicação retornou código $response_code"
    fi
    
    # Testar segurança
    local protected_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/dashboard)
    
    if [ "$protected_response" = "302" ]; then
        log "   ✅ Proteção de segurança ativa (redirecionamento para login)"
    else
        log "   ⚠️  Segurança pode não estar funcionando (código $protected_response)"
    fi
}

# Função para rollback em caso de erro
rollback() {
    log "❌ Erro detectado! Iniciando rollback..."
    
    if [ -f /tmp/last_backup_path ]; then
        local backup_path=$(cat /tmp/last_backup_path)
        
        if [ -d "$backup_path" ]; then
            log "   🔄 Restaurando código do backup..."
            rm -rf "$INSTALL_DIR"
            cp -r "$backup_path/code" "$INSTALL_DIR"
            
            log "   🔄 Restaurando banco de dados..."
            if [ -f "$backup_path/database_backup.sql" ]; then
                sudo -u postgres psql -d assessment_db < "$backup_path/database_backup.sql"
            fi
            
            log "   🔄 Restaurando configurações..."
            if [ -f "$backup_path/assessment.conf" ]; then
                cp "$backup_path/assessment.conf" /etc/supervisor/conf.d/
            fi
            
            if [ -f "$backup_path/.env" ]; then
                cp "$backup_path/.env" "$INSTALL_DIR/"
            fi
            
            log "   🔄 Reiniciando serviços..."
            supervisorctl reread
            supervisorctl update
            supervisorctl restart "$SERVICE_NAME"
            
            log "✅ Rollback concluído! Sistema restaurado ao estado anterior."
        fi
    fi
    
    rm -f /tmp/last_backup_path
}

# Função principal
main() {
    log "🚀 Iniciando deploy com Assessment Público..."
    
    # 1. Criar backup completo
    create_backup
    
    # 2. Verificar mudanças potencialmente perigosas
    if [ -d "$INSTALL_DIR" ]; then
        check_database_changes
    fi
    
    # 3. Parar serviços
    stop_services
    
    # 4. Atualizar código
    update_code
    
    # 5. Configurar ambiente Python
    setup_python_environment
    
    # 6. Configurar banco de dados (preservando dados + migração)
    setup_database
    
    # 7. Configurar Supervisor
    setup_supervisor
    
    # 8. Definir permissões
    set_permissions
    
    # 9. Iniciar serviços
    start_services
    
    # 10. Verificar deployment
    verify_deployment
    
    echo ""
    log "✅ DEPLOY CONCLUÍDO COM SUCESSO!"
    echo ""
    echo "📊 Resumo:"
    echo "   • Código atualizado do Git"
    echo "   • Dados existentes preservados"
    echo "   • Migração de Assessment Público aplicada"
    echo "   • Sistema rodando na porta 8000"
    echo ""
    echo "🔗 Funcionalidades disponíveis:"
    echo "   • Assessments tradicionais (autenticados)"
    echo "   • Assessments públicos (URLs compartilháveis)"
    echo "   • Captura de leads e recomendações IA"
    echo ""
    
    if [ -f /tmp/last_backup_path ]; then
        local backup_path=$(cat /tmp/last_backup_path)
        echo "💾 Backup criado em: $backup_path"
    fi
    
    rm -f /tmp/last_backup_path
}

# Trap para capturar erros e fazer rollback
trap 'rollback' ERR

# Executar
main "$@"
