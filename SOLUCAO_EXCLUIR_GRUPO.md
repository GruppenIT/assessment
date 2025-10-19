# 🔧 SOLUÇÃO: Botão "Excluir" não funciona

## 🎯 **Problema Identificado**

Após análise do relatório de troubleshooting, foram encontrados **2 problemas críticos**:

### 1️⃣ **Merge Conflict no JavaScript** ❌
O arquivo `templates/admin/grupos_lista.html` contém **marcadores de conflito do Git literalmente no código**:

```javascript
function confirmarExclusao(grupoNome, tipoId) {
<<<<<<< Updated upstream        // ← QUEBRA O JAVASCRIPT!
    if (confirm(...)) {
=======
    console.log('DEBUG: ...');
>>>>>>> Stashed changes         // ← TAMBÉM QUEBRA!
```

**Consequência**: O JavaScript é inválido e a função não pode ser executada.

### 2️⃣ **CSRF Token Ausente** ⚠️
O formulário dinâmico não inclui o token CSRF necessário para Flask-WTF aceitar o POST.

**Consequência**: Mesmo se o JavaScript funcionasse, o Flask rejeitaria a requisição.

---

## ✅ **Solução Aplicada no Replit**

Já corrigi ambos os problemas no código:

1. ✅ **Removido** marcadores de conflito do Git
2. ✅ **Adicionado** CSRF token ao formulário dinâmico
3. ✅ **Testado** localmente no Replit

---

## 🚀 **Como Aplicar no Seu Servidor On-Premise**

### **OPÇÃO 1: Script Automático** (RECOMENDADO)

```bash
cd /var/www/assessment
git pull origin main
chmod +x corrigir_merge_conflict_grupos.sh
./corrigir_merge_conflict_grupos.sh
```

Esse script vai:
- ✅ Resolver o merge conflict automaticamente
- ✅ Puxar o código corrigido do repositório
- ✅ Reiniciar o serviço
- ✅ Verificar se tudo está correto

---

### **OPÇÃO 2: Correção Manual** (se preferir)

#### **Passo 1: Resolver o Merge Conflict**

```bash
cd /var/www/assessment
git checkout --theirs templates/admin/grupos_lista.html
git add templates/admin/grupos_lista.html
```

#### **Passo 2: Atualizar do Repositório**

```bash
git pull origin main
```

#### **Passo 3: Reiniciar o Serviço**

```bash
sudo supervisorctl restart assessment
# OU
sudo systemctl restart assessment
```

---

## 🧪 **Como Testar Após Aplicar**

### **1. Teste Básico**

1. Acesse: `http://seu-dominio/admin/grupos`
2. Clique no botão **"Excluir"** de qualquer grupo
3. **DEVE aparecer** um popup de confirmação

### **2. Teste no Console (F12)**

Abra o Console do navegador e digite:

```javascript
typeof confirmarExclusao
```

**Resultado esperado**: `"function"`

**Se retornar `undefined`**:
- Pressione **Ctrl+Shift+R** (hard refresh para limpar cache)
- Teste novamente

### **3. Teste de Exclusão Completa**

1. Clique em **"Excluir"**
2. Confirme no popup
3. A página deve **recarregar**
4. O grupo deve ter sido **removido da lista**
5. Deve aparecer mensagem: **"Grupo [nome] excluído com sucesso!"**

---

## 🔍 **Verificações Adicionais**

### **Verificar se não há mais marcadores de conflito:**

```bash
grep -n "<<<<<<< " templates/admin/grupos_lista.html
```

**Resultado esperado**: `(nenhuma saída)`

### **Verificar se a função existe:**

```bash
grep -A 10 "function confirmarExclusao" templates/admin/grupos_lista.html
```

**Resultado esperado**: Deve mostrar a função completa sem marcadores `<<<<<<<`

### **Verificar se CSRF token está incluído:**

```bash
grep -A 5 "csrf_token" templates/admin/grupos_lista.html
```

**Resultado esperado**: Deve mostrar o código que adiciona o CSRF token

---

## 📋 **Checklist de Aplicação**

Execute no servidor `/var/www/assessment`:

- [ ] `git pull origin main`
- [ ] `./corrigir_merge_conflict_grupos.sh` OU correção manual
- [ ] Aguardar 5 segundos após reiniciar
- [ ] Limpar cache do navegador (Ctrl+Shift+R)
- [ ] Testar exclusão de grupo
- [ ] Confirmar que popup aparece
- [ ] Confirmar que grupo é excluído

---

## 🆘 **Se Ainda Não Funcionar**

Execute e me envie:

```bash
cd /var/www/assessment

# 1. Ver se ainda há marcadores de conflito
grep -n "<<<<<<< " templates/admin/grupos_lista.html

# 2. Ver código atual da função
grep -A 20 "function confirmarExclusao" templates/admin/grupos_lista.html

# 3. Status do serviço
sudo supervisorctl status assessment
```

Envie também:
- Screenshot do Console do navegador (F12) após clicar em "Excluir"
- Mensagem de erro (se houver)

---

## 💡 **Resumo Técnico**

| Item | Antes | Depois |
|------|-------|--------|
| **JavaScript** | Quebrado (merge conflict) | Função válida |
| **CSRF Token** | ❌ Ausente | ✅ Incluído no POST |
| **Funcionamento** | ❌ Nada acontece | ✅ Popup + Exclusão |

---

## 📝 **Arquivos Corrigidos**

- `templates/admin/grupos_lista.html` - Função JavaScript + CSRF token

---

**Execute `./corrigir_merge_conflict_grupos.sh` e me avise o resultado!** 🚀
