-- Migração para adicionar funcionalidade de assessment público
-- Data: 2025-10-11

-- Adicionar campo url_publica nas tabelas de tipos de assessment
-- (sistema antigo e novo com versionamento)
ALTER TABLE tipos_assessment ADD COLUMN IF NOT EXISTS url_publica BOOLEAN DEFAULT FALSE;
ALTER TABLE assessment_tipos ADD COLUMN IF NOT EXISTS url_publica BOOLEAN DEFAULT FALSE;

-- Adicionar campo telefone nas tabelas respondentes e clientes
ALTER TABLE respondentes ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);

-- Criar tabela de assessments públicos
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

-- Criar índice no token para busca rápida
CREATE INDEX IF NOT EXISTS idx_assessments_publicos_token ON assessments_publicos(token);

-- Criar tabela de respostas públicas
CREATE TABLE IF NOT EXISTS respostas_publicas (
    id SERIAL PRIMARY KEY,
    assessment_publico_id INTEGER NOT NULL REFERENCES assessments_publicos(id) ON DELETE CASCADE,
    pergunta_id INTEGER NOT NULL REFERENCES perguntas(id),
    valor INTEGER NOT NULL CHECK (valor IN (0, 3, 5)),
    data_resposta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_assessment_pergunta_publica UNIQUE (assessment_publico_id, pergunta_id)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_respostas_publicas_assessment ON respostas_publicas(assessment_publico_id);
CREATE INDEX IF NOT EXISTS idx_respostas_publicas_pergunta ON respostas_publicas(pergunta_id);

-- Comentários nas tabelas
COMMENT ON TABLE assessments_publicos IS 'Armazena assessments respondidos publicamente sem autenticação';
COMMENT ON TABLE respostas_publicas IS 'Respostas individuais de assessments públicos';
COMMENT ON COLUMN tipos_assessment.url_publica IS 'Se o assessment possui URL pública habilitada';
COMMENT ON COLUMN assessments_publicos.token IS 'Token único para acessar o resultado do assessment';
COMMENT ON COLUMN respostas_publicas.valor IS 'Valor da resposta: 0=Não, 3=Parcial, 5=Sim';
