# Atualização On-Premise - Sistema de Auditoria

## Problema Identificado
O sistema on-premise está apresentando erro devido à falta da tabela `auditoria` no banco SQLite:

```
ERROR:root:Erro no dashboard: (sqlite3.OperationalError) no such table: auditoria
```

## Solução

### 1. Script de Migração Criado
Foi criado o arquivo `migration_auditoria.py` que:
- Cria a tabela `auditoria` com todos os campos necessários
- Cria a tabela `configuracoes` se não existir
- Adiciona índices para melhor performance
- Funciona com SQLite (ambiente on-premise)

### 2. Deploy Atualizado
O arquivo `deploy-updated.sh` foi atualizado para:
- Executar automaticamente a migração após instalar dependências
- Verificar se as tabelas foram criadas corretamente

### 3. Executar Manualmente (se necessário)

Se você já rodou o deploy e ainda tem o erro, execute apenas:

```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python migration_auditoria.py"
```

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