# 🚨 CORREÇÃO EMERGENCIAL - PERFIL ON-PREMISE

## Problema
Internal Server Error persistente na página `/auth/perfil` no ambiente on-premise.

## Soluções Disponíveis

### 1. 🔍 INVESTIGAÇÃO COMPLETA
```bash
curl -O https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/investigar_erro_perfil.py
sudo python3 investigar_erro_perfil.py
```

**O que faz:**
- Verifica logs do supervisor e aplicação
- Testa ambiente Python e dependências
- Analisa imports e rotas
- Verifica banco de dados e templates
- Gera relatório detalhado

### 2. 🔧 CORREÇÃO RADICAL
```bash
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/correcao_radical_perfil.sh | sudo bash
```

**O que faz:**
- Para o serviço completamente
- Recria arquivo `routes/auth.py` do zero
- Recria template `perfil.html` simplificado
- Remove funcionalidade de alteração de senha temporariamente
- Ajusta permissões e limpa cache
- Reinicia serviços e testa

### 3. 🛠️ CORREÇÃO SIMPLES (Já tentada)
```bash
curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/fix_perfil_onpremise.sh | sudo bash
```

## Estratégia de Diagnóstico

1. **Execute primeiro a investigação:**
   ```bash
   curl -O https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/investigar_erro_perfil.py
   sudo python3 investigar_erro_perfil.py
   ```

2. **Se a investigação não resolver, use a correção radical:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/GruppenIT/assessment/refs/heads/main/correcao_radical_perfil.sh | sudo bash
   ```

## Possíveis Causas do Problema

1. **Dependências incompatíveis** - Versões do Flask/WTForms
2. **Imports circulares** - Problemas na estrutura de imports
3. **Contexto de aplicação** - FlaskForm fora do contexto
4. **Permissões de arquivo** - www-data sem acesso
5. **Cache Python** - Arquivos .pyc corrompidos
6. **Configuração supervisor** - Ambiente virtual incorreto

## Verificações Manuais

### Logs
```bash
# Logs do supervisor
tail -f /var/log/supervisor/supervisord.log

# Logs da aplicação
tail -f /var/log/supervisor/assessment-*.log

# Status do serviço
supervisorctl status assessment
```

### Teste direto
```bash
cd /var/www/assessment
source venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from routes.auth import auth_bp
    print('✅ Import OK')
except Exception as e:
    print(f'❌ Erro: {e}')
"
```

### Permissões
```bash
ls -la /var/www/assessment/routes/auth.py
ls -la /var/www/assessment/templates/auth/perfil.html
```

## Backup e Recuperação

Todos os scripts fazem backup automático:
- **Investigação**: Não altera arquivos
- **Correção radical**: Backup em `/tmp/backup_YYYYMMDD_HHMMSS/`

Para reverter:
```bash
# Encontrar backup mais recente
ls -la /tmp/backup_*

# Restaurar (substitua pela data correta)
sudo cp -r /tmp/backup_20241230_120000/routes/* /var/www/assessment/routes/
sudo cp -r /tmp/backup_20241230_120000/templates/* /var/www/assessment/templates/
sudo supervisorctl restart assessment
```

## Contato

Se nenhuma solução funcionar, forneça:
1. Saída completa do script de investigação
2. Logs do supervisor
3. Versão do Python e dependências
4. Configuração do ambiente virtual

---

**Última atualização:** $(date)
**Versão:** 2.0 - Correção Radical