-- Migração: Adicionar coluna 'grupo' à tabela assessments_publicos
-- Data: 2025-10-17
-- Descrição: Adiciona campo para armazenar grupo/campanha de assessments públicos

-- Verificar e adicionar coluna 'grupo' se não existir
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'assessments_publicos' 
        AND column_name = 'grupo'
    ) THEN
        ALTER TABLE assessments_publicos 
        ADD COLUMN grupo VARCHAR(100);
        
        COMMENT ON COLUMN assessments_publicos.grupo IS 'Grupo/Campanha do assessment (parâmetro ?group=xyz)';
        
        RAISE NOTICE 'Coluna grupo adicionada com sucesso à tabela assessments_publicos';
    ELSE
        RAISE NOTICE 'Coluna grupo já existe na tabela assessments_publicos';
    END IF;
END $$;

-- Criar índice para melhorar performance das queries de grupo (opcional mas recomendado)
CREATE INDEX IF NOT EXISTS idx_assessments_publicos_grupo 
ON assessments_publicos(grupo) 
WHERE grupo IS NOT NULL;

COMMENT ON INDEX idx_assessments_publicos_grupo IS 'Índice para otimizar queries de agrupamento de assessments públicos';
