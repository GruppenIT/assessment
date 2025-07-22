# Atualização On-Premise - Sistema de Auditoria

## Problema Identificado
O sistema on-premise está apresentando erro devido à falta da tabela `auditoria` no banco SQLite:

```
ERROR:root:Erro no dashboard: (sqlite3.OperationalError) no such table: auditoria
```

## SOLUÇÃO DEFINITIVA POSTGRESQL

### 1. Script Específico para PostgreSQL
Foi criado o arquivo `fix_auditoria_postgresql.py` que:
- Conecta no PostgreSQL usando as configurações do .env
- Cria a tabela `auditoria` com todos os campos necessários
- Cria a tabela `configuracoes` se não existir  
- Adiciona índices para melhor performance
- Verifica se as tabelas foram criadas corretamente

### 2. EXECUTAR AGORA (POSTGRESQL ON-PREMISE)

**Opção 1: Script Automático (requer .env configurado)**
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python fix_auditoria_postgresql.py"
sudo supervisorctl restart assessment
```

**Opção 2: Script Manual (se .env não estiver configurado)**
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python fix_auditoria_postgresql_manual.py"
sudo supervisorctl restart assessment
```

### 3. DIAGNÓSTICO COMPLETO (se ainda houver problemas)

**Primeiro, execute o diagnóstico para identificar o problema:**
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python verify_env_config.py"
```

Este script vai verificar:
- Se arquivo .env existe e está configurado corretamente
- Se DATABASE_URL aponta para PostgreSQL ou SQLite
- Se as variáveis de ambiente estão carregadas
- Se a conexão PostgreSQL funciona

### 4. Verificar Conexão PostgreSQL (se necessário)

Se der erro de conexão, verifique:

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar se usuário e banco existem
sudo -u postgres psql -c "\l" | grep assessment
sudo -u postgres psql -c "\du" | grep assessment
```

### 4. Scripts Alternativos

Para SQLite (desenvolvimento):
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python fix_auditoria_onpremise.py"
```

Para migração genérica:
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python migration_auditoria.py"
```

## PROBLEMA IDENTIFICADO: .ENV NÃO CARREGADO

O diagnóstico mostrou que:
- ✓ Arquivo .env existe e está correto  
- ✗ Variáveis de ambiente não estão sendo carregadas
- ✗ Aplicação usa SQLite como fallback

**CAUSA**: Supervisor não está carregando o arquivo .env

### 5. CORREÇÃO DEFINITIVA - CARREGAR .ENV

Execute o script de correção:
```bash
cd /var/www/assessment
sudo python fix_env_loading.py
```

Este script vai:
- Carregar todas as variáveis do .env
- Atualizar configuração do supervisor
- Reiniciar os serviços automaticamente
- Aplicar as variáveis de ambiente corretamente

### 6. CORREÇÃO SUPERVISOR (se houver erro de formatação)

Se o supervisor apresentar erro de formato, execute:
```bash
cd /var/www/assessment
sudo python fix_supervisor_config.py
```

### 7. TESTAR CONEXÃO

Para verificar se tudo está funcionando:
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python test_database_connection.py"
```

### 8. SOLUÇÃO DEFINITIVA - MODIFICAR CÓDIGO

Se o problema persistir (aplicação ainda usando SQLite), execute:

**Debug completo:**
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python debug_environment.py"
```

**Aplicar correção permanente:**
```bash
cd /var/www/assessment
sudo python apply_env_permanently.py
```

Este script vai:
- Criar módulo que carrega .env automaticamente
- Modificar main.py e app.py para importar o carregador
- Garantir que DATABASE_URL seja sempre carregada

### 9. TESTE FINAL

Após aplicar todas as correções, execute o teste final:
```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python final_test_onpremise.py"
```

Este teste vai confirmar se:
- PostgreSQL está conectado
- Tabela auditoria existe
- Sistema está totalmente operacional

### 4. Verificar Resultado

Após executar, você deve ver:
```
✓ Tabela auditoria criada com sucesso!
✓ Índices criados com sucesso!
✓ Tabela configuracoes já existe (ou criada)
✅ Migração concluída com sucesso!
```

### 5. Reiniciar Serviço

```bash
sudo supervisorctl restart assessment
```

## Características da Tabela Auditoria

- **ID**: Chave primária autoincremental
- **Usuário**: Tipo, ID, nome e email do usuário
- **Ação**: Tipo de operação (create, update, delete, login, etc.)
- **Entidade**: Que foi modificada (cliente, projeto, resposta, etc.)
- **Detalhes**: Descrição e metadados da ação
- **Metadata**: IP, user agent, timestamp

## Próximos Passos

Após a correção, o sistema de auditoria estará disponível e o dashboard voltará a funcionar normalmente sem erros.