# 🔍 Como Diagnosticar Problemas de E-mail

## ⚡ Diagnóstico Rápido

### 1. Execute o script de diagnóstico

```bash
cd /var/www/assessment
python3 diagnostico_email.py
```

O script irá verificar:
- ✅ Configurações SMTP salvas no banco
- ✅ Tipos de assessment com destinatários configurados
- ✅ Leads criados recentemente
- ✅ Testar envio de e-mail

### 2. Verificar logs em tempo real

```bash
# Ver todos os logs
sudo supervisorctl tail -f assessment stdout

# Filtrar apenas logs de e-mail
sudo supervisorctl tail -f assessment stdout | grep -i "email\|smtp\|lead"

# Ver erros
sudo supervisorctl tail -f assessment stderr
```

## 🔎 Checklist de Verificação

### ☑️ 1. Configurações SMTP

Acesse: `/admin/parametros/smtp`

**Verifique se todos os campos estão preenchidos:**

**Para autenticação básica:**
- [ ] Servidor SMTP (ex: smtp.gmail.com)
- [ ] Porta (ex: 587)
- [ ] Usuário SMTP
- [ ] Senha SMTP
- [ ] E-mail remetente
- [ ] Nome do remetente

**Para OAuth2 Microsoft 365:**
- [ ] Servidor SMTP (ex: smtp.office365.com)
- [ ] Porta (ex: 587)
- [ ] Client ID
- [ ] Client Secret
- [ ] Refresh Token
- [ ] Tenant ID
- [ ] E-mail remetente
- [ ] Nome do remetente

### ☑️ 2. Destinatários Configurados

Vá em: `Assessments → Editar Tipo`

- [ ] Campo "E-mails para Notificação de Leads" preenchido
- [ ] E-mails separados por vírgula ou ponto-e-vírgula
- [ ] E-mails válidos (sem espaços extras)

Exemplo correto:
```
vendas@empresa.com, comercial@empresa.com
```

### ☑️ 3. Assessment com URL Pública

- [ ] Assessment marcado como "URL Pública Ativada"
- [ ] Token de acesso gerado

### ☑️ 4. Lead Criado

Verifique se o lead foi salvo:
```bash
sudo -u postgres psql -d assessment_db -c "SELECT id, nome, email, data_criacao FROM leads ORDER BY data_criacao DESC LIMIT 5;"
```

## 🐛 Problemas Comuns e Soluções

### Problema 1: "E-mail não está sendo enviado"

**Verificar:**
```bash
# Ver logs de erro
sudo supervisorctl tail -100 assessment stdout | grep -i error

# Ver se o módulo de e-mail foi carregado
python3 -c "from utils.email_utils import EmailSender; print('OK')"
```

**Solução:**
- Verifique se MSAL está instalado: `pip3 show msal`
- Reinstale se necessário: `pip3 install msal`

### Problema 2: "Erro de autenticação SMTP"

**Para Gmail:**
- Use "Senha de app" ao invés da senha normal
- Ative "Acesso de apps menos seguros" (não recomendado)
- Use OAuth2

**Para Microsoft 365:**
- Verifique se o Client ID está correto
- Verifique se o Refresh Token não expirou
- Use o servidor correto (não smtp.office365.com direto, use o relay)

### Problema 3: "Campo email_destinatarios não existe"

**Verificar:**
```bash
sudo -u postgres psql -d assessment_db -c "\d assessment_tipos" | grep email_destinatarios
```

**Se não aparecer, criar:**
```bash
sudo -u postgres psql -d assessment_db -c "ALTER TABLE assessment_tipos ADD COLUMN email_destinatarios TEXT;"
```

### Problema 4: "Lead criado mas e-mail não enviado"

**Causas possíveis:**
1. Campo `email_destinatarios` vazio no tipo de assessment
2. Erro no envio (ver logs)
3. E-mail foi para spam

**Testar manualmente:**
```python
python3 <<EOF
from app import app
from models.leads import Lead
from utils.email_utils import enviar_alerta_novo_lead

with app.app_context():
    # Pegar último lead
    lead = Lead.query.order_by(Lead.id.desc()).first()
    
    if lead:
        print(f"Testando envio para lead #{lead.id}: {lead.nome}")
        print(f"Tipo: {lead.tipo_assessment.nome}")
        print(f"Destinatários: {lead.tipo_assessment.email_destinatarios}")
        
        resultado = enviar_alerta_novo_lead(lead, lead.tipo_assessment)
        print(f"Resultado: {'Enviado!' if resultado else 'Falhou'}")
    else:
        print("Nenhum lead encontrado")
EOF
```

## 📊 Comandos Úteis

### Ver configurações SMTP do banco
```python
python3 <<EOF
from app import app
from models.parametro_sistema import ParametroSistema

with app.app_context():
    config = ParametroSistema.get_smtp_config()
    for key, value in config.items():
        if 'password' not in key and 'secret' not in key and 'token' not in key:
            print(f"{key}: {value}")
EOF
```

### Ver tipos com destinatários
```python
python3 <<EOF
from app import app
from models.assessment_version import AssessmentTipo

with app.app_context():
    tipos = AssessmentTipo.query.filter(AssessmentTipo.url_publica == True).all()
    
    for tipo in tipos:
        print(f"\nTipo: {tipo.nome}")
        print(f"  URL Pública: {'Sim' if tipo.url_publica else 'Não'}")
        print(f"  Destinatários: {tipo.email_destinatarios or 'NENHUM'}")
EOF
```

### Testar envio simples
```python
python3 <<EOF
from app import app
from utils.email_utils import EmailSender

with app.app_context():
    sender = EmailSender()
    
    resultado = sender.enviar_email(
        destinatarios=['seu-email@exemplo.com'],
        assunto='Teste de E-mail',
        corpo_html='<h1>Teste funcionando!</h1>'
    )
    
    print('Enviado com sucesso!' if resultado else 'Falhou!')
EOF
```

## 📋 Fluxo de Envio Esperado

Quando um lead é criado via assessment público:

1. ✅ Lead salvo no banco de dados
2. ✅ Sistema busca `tipo_assessment.email_destinatarios`
3. ✅ Se houver destinatários:
   - Busca configurações SMTP do banco
   - Gera HTML do e-mail com dados do lead
   - Envia para cada destinatário
   - Loga resultado (sucesso ou erro)
4. ✅ Redireciona para página de resultado

**Os logs devem mostrar:**
```
INFO: Tentando enviar alerta de lead para: email1@exemplo.com, email2@exemplo.com
INFO: E-mail enviado com sucesso via [SMTP básico/OAuth2] para email1@exemplo.com, email2@exemplo.com
```

**Ou em caso de erro:**
```
ERROR: Erro ao enviar e-mail: [mensagem de erro]
```

## 🔧 Resolver Problemas Passo a Passo

### Passo 1: Confirmar instalação do MSAL
```bash
pip3 install msal
sudo supervisorctl restart assessment
```

### Passo 2: Confirmar coluna existe
```bash
sudo -u postgres psql -d assessment_db <<EOF
ALTER TABLE assessment_tipos ADD COLUMN IF NOT EXISTS email_destinatarios TEXT;
EOF
```

### Passo 3: Executar diagnóstico
```bash
python3 diagnostico_email.py
```

### Passo 4: Testar manualmente
- Digite um e-mail de teste quando solicitado
- Verifique a caixa de entrada (inclusive spam)

### Passo 5: Se ainda não funcionar
```bash
# Ver logs completos
sudo supervisorctl tail -200 assessment stdout > /tmp/assessment_logs.txt
cat /tmp/assessment_logs.txt | grep -i "email\|smtp\|lead\|error"
```

Envie os logs para análise.

---

**Criado em**: 13/10/2025
