-- Migration: Adicionar campo cta_texto ao assessment_tipos
-- Data: 2025-10-13
-- Descrição: Adiciona campo de texto personalizado para CTA em cada tipo de assessment

-- Adicionar coluna cta_texto se não existir
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'assessment_tipos' 
        AND column_name = 'cta_texto'
    ) THEN
        ALTER TABLE assessment_tipos 
        ADD COLUMN cta_texto TEXT;
        
        -- Adicionar comentário à coluna
        COMMENT ON COLUMN assessment_tipos.cta_texto IS 'Texto personalizado do CTA para este tipo de assessment';
        
        RAISE NOTICE 'Coluna cta_texto adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna cta_texto já existe';
    END IF;
END $$;
