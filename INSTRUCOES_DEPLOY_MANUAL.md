# Deployment Manual do Sistema de Leads

## Problema Identificado

Os scripts estão corrompendo durante a transferência SCP. Vamos fazer o deployment manualmente.

## Solução: Executar Comandos Diretamente

### Passo 1: Conectar ao Servidor

```bash
ssh root@vlxweb12
```

### Passo 2: Fazer Backup do Banco

```bash
cd /var/www/assessment
mkdir -p backups
sudo -u postgres pg_dump assessment_db > backups/backup_leads_$(date +%Y%m%d_%H%M%S).sql
ls -lh backups/backup_leads_*
```

### Passo 3: Parar Aplicação

```bash
sudo supervisorctl stop assessment
```

### Passo 4: Atualizar Código do Git

```bash
cd /var/www/assessment
git stash
git pull origin main
```

### Passo 5: Criar Tabelas SQL (copie e cole tudo de uma vez)

```bash
sudo -u postgres psql -d assessment_db << 'EOF'
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

SELECT 'Tabelas criadas com sucesso!' AS status;
EOF
```

### Passo 6: Verificar Tabelas Criadas

```bash
sudo -u postgres psql -d assessment_db -c "\d leads"
sudo -u postgres psql -d assessment_db -c "\d leads_historico"
```

### Passo 7: Reiniciar Aplicação

```bash
sudo supervisorctl start assessment
sleep 3
sudo supervisorctl status assessment
```

### Passo 8: Verificar Logs

```bash
sudo supervisorctl tail assessment stderr | tail -50
```

### Passo 9: Testar Acesso

```bash
curl -I https://assessments.zerobox.com.br/admin/leads
```

## Verificação Final

Se tudo correu bem, você verá:

- ✅ Tabelas `leads` e `leads_historico` criadas
- ✅ Aplicação rodando (status RUNNING)
- ✅ Sem erros nos logs
- ✅ Dashboard de leads acessível

## Em Caso de Erro

Se algo der errado, restaure o backup:

```bash
sudo supervisorctl stop assessment
sudo -u postgres psql -d assessment_db < backups/backup_leads_YYYYMMDD_HHMMSS.sql
sudo supervisorctl start assessment
```

## Próximos Passos

Após deployment bem-sucedido:

1. Acesse: https://assessments.zerobox.com.br/admin/leads
2. Responda um assessment público para gerar um lead de teste
3. Gerencie os leads pelo dashboard

---

**IMPORTANTE:** Copie e cole cada bloco de comando de uma vez só para evitar problemas de encoding.
