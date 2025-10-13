-- Migration: Adicionar configurações SMTP ao sistema
-- Data: 2025-10-13
-- Descrição: Adiciona parâmetros de configuração SMTP para envio de e-mails

-- As configurações serão armazenadas na tabela parametros_sistema existente
-- Este script apenas documenta as chaves que serão usadas

-- Configurações SMTP que serão gerenciadas via ParametroSistema:
-- smtp_server: Servidor SMTP (string)
-- smtp_port: Porta SMTP (string)
-- smtp_use_tls: Usar TLS/SSL (string: 'true' ou 'false')
-- smtp_auth_type: Tipo de autenticação (string: 'oauth2' ou 'basic')
-- smtp_client_id: Client ID OAuth2 (encrypted)
-- smtp_client_secret: Client Secret OAuth2 (encrypted)
-- smtp_refresh_token: Refresh Token OAuth2 (encrypted)
-- smtp_tenant_id: Tenant ID Microsoft (string)
-- smtp_from_email: E-mail remetente (string)
-- smtp_from_name: Nome do remetente (string)
-- smtp_username: Usuário SMTP para autenticação básica (string)
-- smtp_password: Senha SMTP para autenticação básica (encrypted)

-- Valores padrão serão inseridos via código Python ao acessar a página de configuração
