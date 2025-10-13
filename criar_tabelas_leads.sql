-- Script SQL para criar tabelas do Sistema de Leads
-- Execute com: sudo -u postgres psql -d assessment_db -f criar_tabelas_leads.sql

BEGIN;

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

-- Indices para performance
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_prioridade ON leads(prioridade);
CREATE INDEX IF NOT EXISTS idx_leads_data_criacao ON leads(data_criacao DESC);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_empresa ON leads(empresa);

-- Criar tabela de historico
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

-- Indice para historico
CREATE INDEX IF NOT EXISTS idx_historico_lead ON leads_historico(lead_id, data_registro DESC);

-- Comentarios
COMMENT ON TABLE leads IS 'Tabela de leads gerados por assessments publicos';
COMMENT ON TABLE leads_historico IS 'Historico de interacoes e mudancas nos leads';

COMMIT;

-- Verificacao
SELECT 'Tabela leads criada com sucesso!' AS status, COUNT(*) AS colunas 
FROM information_schema.columns 
WHERE table_name = 'leads';

SELECT 'Tabela leads_historico criada com sucesso!' AS status, COUNT(*) AS colunas 
FROM information_schema.columns 
WHERE table_name = 'leads_historico';
