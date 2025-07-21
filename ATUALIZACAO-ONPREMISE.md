# Atualização On-Premise - Sistema de Auditoria

## Problema Identificado
O sistema on-premise está apresentando erro devido à falta da tabela `auditoria` no banco SQLite:

```
ERROR:root:Erro no dashboard: (sqlite3.OperationalError) no such table: auditoria
```

## SOLUÇÃO DEFINITIVA

### 1. Script de Correção Específico
Foi criado o arquivo `fix_auditoria_onpremise.py` que:
- Detecta automaticamente o caminho correto do banco SQLite
- Cria a tabela `auditoria` com todos os campos necessários
- Cria a tabela `configuracoes` se não existir
- Adiciona índices para melhor performance
- Verifica se as tabelas foram criadas corretamente

### 2. EXECUTAR AGORA (SOLUÇÃO IMEDIATA)

No servidor on-premise, execute:

```bash
cd /var/www/assessment
sudo bash -c "source venv/bin/activate && python fix_auditoria_onpremise.py"
sudo supervisorctl restart assessment
```

### 3. Script Alternativo (se o acima não funcionar)

Se ainda houver problemas, use o script original:

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