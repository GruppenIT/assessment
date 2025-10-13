-- Migration: Adicionar campo de destinatários de e-mail aos tipos de assessment
-- Data: 2025-10-13
-- Descrição: Adiciona campo para armazenar e-mails que receberão alertas de novos leads

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'assessment_tipos' 
        AND column_name = 'email_destinatarios'
    ) THEN
        ALTER TABLE assessment_tipos 
        ADD COLUMN email_destinatarios TEXT;
        
        COMMENT ON COLUMN assessment_tipos.email_destinatarios IS 
        'E-mails que receberão alertas de novos leads (separados por vírgula ou ponto-e-vírgula)';
        
        RAISE NOTICE 'Coluna email_destinatarios adicionada com sucesso';
    ELSE
        RAISE NOTICE 'Coluna email_destinatarios já existe';
    END IF;
END $$;
