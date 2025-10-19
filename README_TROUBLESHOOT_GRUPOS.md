# 🔧 Troubleshooting: Botão "Excluir" não funciona em /admin/grupos

## Problema

Quando você clica no botão "Excluir" para remover um grupo na página `/admin/grupos`, nada acontece.

## Solução Rápida: Atualizar Código

**PRIMEIRO PASSO**: Atualizar o código no servidor (pode ser que o código esteja desatualizado)

```bash
cd /var/www/assessment
./atualizar_codigo_grupos.sh
```

Este script irá:
- ✅ Fazer backup dos arquivos atuais
- ✅ Puxar atualizações do Git
- ✅ Verificar se as funções necessárias existem
- ✅ Reiniciar o serviço automaticamente

Após a atualização:
1. Aguarde 5 segundos
2. Acesse `/admin/grupos` no navegador
3. Tente clicar em "Excluir" novamente

---

## Se AINDA não funcionar: Diagnóstico Completo

Execute o script de troubleshooting:

```bash
cd /var/www/assessment
./troubleshoot_excluir_grupo.sh
```

Este script irá:
- 🔍 Verificar se o código está atualizado
- 🔍 Verificar se a rota `/admin/grupos/<tag>/<tipo_id>/delete` existe
- 🔍 Verificar se a função JavaScript `confirmarExclusao()` existe
- 🔍 Verificar se o botão tem o `onclick` correto
- 🔍 Verificar se há CSRF token
- 🔍 Verificar logs do Flask
- 🔍 Verificar grupos no banco de dados
- 📝 Gerar relatório completo em `/tmp/troubleshoot_excluir_grupo_*.txt`

### Enviar Relatório

Após executar o script, ele criará um arquivo de relatório. Para visualizar:

```bash
cat /tmp/troubleshoot_excluir_grupo_*.txt
```

**Copie TODO o conteúdo** e envie para análise.

---

## Teste Manual no Navegador

Enquanto aguarda ou depois de rodar os scripts, você pode fazer este teste:

### 1. Abrir Console do Navegador

1. Acesse `/admin/grupos`
2. Pressione **F12** (ou Ctrl+Shift+I)
3. Vá para a aba **Console**

### 2. Clicar em "Excluir"

Clique no botão "Excluir" de qualquer grupo e observe o console.

### 3. Possíveis Erros

| Erro no Console | Causa | Solução |
|----------------|-------|---------|
| `confirmarExclusao is not defined` | Função JavaScript não carregada | Template desatualizado |
| `Cannot read property 'value' of null` | CSRF token ausente | Falta campo hidden no form |
| `405 Method Not Allowed` | Rota não aceita POST | Rota não configurada corretamente |
| `404 Not Found` | Rota não existe | Código desatualizado |
| Nada acontece (sem erro) | Problema com aspas no onclick | Template com sintaxe incorreta |

### 4. Testar Função Manualmente

Cole isto no Console do Navegador:

```javascript
// 1. Verificar se a função existe
console.log(typeof confirmarExclusao);  // Deve retornar "function"

// 2. Verificar CSRF token
console.log(document.querySelector('input[name="csrf_token"]'));  // Deve retornar um elemento <input>

// 3. Testar função (substitua 'teste' e 1 por valores reais de um grupo)
confirmarExclusao('teste', 1);
```

**Resultado esperado**: Deve aparecer um popup de confirmação.

---

## Verificar Código-Fonte da Página

1. Na página `/admin/grupos`, pressione **Ctrl+U** (ver código-fonte)
2. Procure por:

### a) Função JavaScript (deve existir)
```javascript
function confirmarExclusao(grupoNome, tipoId) {
    if (confirm('Tem certeza que deseja excluir...')) {
        // ...código...
    }
}
```

### b) Botão com onclick (deve estar assim)
```html
<button onclick='confirmarExclusao("nome_do_grupo", 123)'>Excluir</button>
```

**IMPORTANTE**: O `onclick` deve usar aspas **simples** (`'`) por fora.

### c) CSRF Token (deve existir)
```html
<input type="hidden" name="csrf_token" value="...">
```

---

## Checklist de Diagnóstico

- [ ] Rodei `./atualizar_codigo_grupos.sh`
- [ ] Aguardei 5 segundos após reiniciar
- [ ] Testei no navegador
- [ ] Abri o Console (F12)
- [ ] Vi se há erros no console
- [ ] Rodei `./troubleshoot_excluir_grupo.sh`
- [ ] Copiei o relatório completo
- [ ] Verifiquei código-fonte da página (Ctrl+U)
- [ ] Testei função manualmente no console

---

## Arquivos Envolvidos

| Arquivo | Função |
|---------|--------|
| `routes/admin.py` | Contém rota `excluir_grupo()` |
| `templates/admin/grupos_lista.html` | Contém botão e função JavaScript |
| `templates/admin/grupos_estatisticas.html` | Página de estatísticas |

---

## Scripts Disponíveis

| Script | Quando Usar |
|--------|-------------|
| `atualizar_codigo_grupos.sh` | **SEMPRE PRIMEIRO** - Atualiza código |
| `troubleshoot_excluir_grupo.sh` | Se atualização não resolver |
| `aplicar_grupos_filtros_exclusao_geral.sh` | Deployment inicial (já foi rodado?) |

---

## Contato

Após rodar os scripts e fazer os testes, envie:

1. ✅ Relatório completo do `troubleshoot_excluir_grupo.sh`
2. ✅ Erros que aparecem no Console do navegador (F12)
3. ✅ Screenshot da página `/admin/grupos`
4. ✅ Resultado dos testes manuais no console
