#!/bin/bash

###############################################################################
# Script de Troubleshooting: Botão "Excluir" não funciona em /admin/grupos
# 
# Este script diagnostica problemas com a exclusão de grupos
###############################################################################

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_FILE="/tmp/troubleshoot_excluir_grupo_$(date +%Y%m%d_%H%M%S).txt"

echo "======================================================================"
echo "TROUBLESHOOTING: Botão Excluir Grupo"
echo "======================================================================"
echo ""
echo "Gerando relatório em: $REPORT_FILE"
echo ""

# Função para log
log_section() {
    echo "" | tee -a "$REPORT_FILE"
    echo "======================================================================" | tee -a "$REPORT_FILE"
    echo "$1" | tee -a "$REPORT_FILE"
    echo "======================================================================" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$REPORT_FILE"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1" | tee -a "$REPORT_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$REPORT_FILE"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1" | tee -a "$REPORT_FILE"
}

# Verificar diretório
if [ ! -f "app.py" ]; then
    log_error "Execute no diretório raiz do projeto (/var/www/assessment)"
    exit 1
fi

log_section "1. INFORMAÇÕES DO AMBIENTE"
log_info "Diretório: $(pwd)"
log_info "Data/Hora: $(date)"
log_info "Usuário: $(whoami)"
echo ""

# Verificar Git
log_section "2. STATUS DO GIT"
git status | tee -a "$REPORT_FILE"
echo ""
log_info "Último commit:"
git log -1 --oneline | tee -a "$REPORT_FILE"
echo ""

# Verificar rota de exclusão
log_section "3. VERIFICAR ROTA DE EXCLUSÃO"
log_info "Procurando rota 'excluir_grupo' em routes/admin.py..."
if grep -n "def excluir_grupo" routes/admin.py > /dev/null 2>&1; then
    log_success "Rota excluir_grupo encontrada:"
    grep -n "def excluir_grupo" routes/admin.py | tee -a "$REPORT_FILE"
    echo ""
    log_info "Conteúdo da rota:"
    grep -A 30 "def excluir_grupo" routes/admin.py | tee -a "$REPORT_FILE"
else
    log_error "Rota excluir_grupo NÃO encontrada em routes/admin.py!"
fi
echo ""

# Verificar registro da rota
log_section "4. VERIFICAR REGISTRO DA ROTA"
log_info "Procurando @admin_bp.route com /delete..."
if grep -n "grupos/<.*>/delete" routes/admin.py > /dev/null 2>&1; then
    log_success "Rota registrada:"
    grep -n "grupos/<.*>/delete" routes/admin.py | tee -a "$REPORT_FILE"
else
    log_error "Rota de exclusão NÃO está registrada!"
fi
echo ""

# Verificar função JavaScript
log_section "5. VERIFICAR FUNÇÃO JAVASCRIPT confirmarExclusao()"
log_info "Procurando função confirmarExclusao em templates/admin/grupos_lista.html..."
if grep -n "function confirmarExclusao" templates/admin/grupos_lista.html > /dev/null 2>&1; then
    log_success "Função JavaScript encontrada:"
    grep -A 20 "function confirmarExclusao" templates/admin/grupos_lista.html | tee -a "$REPORT_FILE"
else
    log_error "Função confirmarExclusao() NÃO encontrada no template!"
fi
echo ""

# Verificar botão de exclusão
log_section "6. VERIFICAR BOTÃO DE EXCLUSÃO"
log_info "Procurando botão com onclick='confirmarExclusao...'..."
if grep -n "onclick.*confirmarExclusao" templates/admin/grupos_lista.html > /dev/null 2>&1; then
    log_success "Botão encontrado:"
    grep -B 2 -A 2 "onclick.*confirmarExclusao" templates/admin/grupos_lista.html | tee -a "$REPORT_FILE"
else
    log_error "Botão de exclusão NÃO encontrado!"
fi
echo ""

# Verificar CSRF token
log_section "7. VERIFICAR CSRF TOKEN NO FORM"
log_info "Procurando hidden input com csrf_token..."
if grep -n "csrf_token" templates/admin/grupos_lista.html > /dev/null 2>&1; then
    log_success "CSRF token encontrado:"
    grep -n "csrf_token" templates/admin/grupos_lista.html | tee -a "$REPORT_FILE"
else
    log_warning "CSRF token pode estar ausente no template!"
fi
echo ""

# Verificar se há grupos para testar
log_section "8. VERIFICAR GRUPOS EXISTENTES NO BANCO"
log_info "Consultando grupos no banco de dados..."
psql "$DATABASE_URL" -c "
SELECT grupo, tipo_assessment_id, COUNT(*) as total
FROM assessment_publico 
WHERE grupo IS NOT NULL 
GROUP BY grupo, tipo_assessment_id 
ORDER BY grupo, tipo_assessment_id 
LIMIT 10;
" 2>&1 | tee -a "$REPORT_FILE"
echo ""

# Verificar logs recentes
log_section "9. VERIFICAR LOGS RECENTES DO FLASK"
log_info "Últimas 50 linhas do log do Flask..."
if [ -f "/var/log/assessment/error.log" ]; then
    tail -50 /var/log/assessment/error.log | tee -a "$REPORT_FILE"
elif [ -f "/var/log/supervisor/assessment-stderr.log" ]; then
    tail -50 /var/log/supervisor/assessment-stderr.log | tee -a "$REPORT_FILE"
else
    log_warning "Não foi possível encontrar o arquivo de log"
fi
echo ""

# Verificar status do serviço
log_section "10. STATUS DO SERVIÇO"
if command -v supervisorctl &> /dev/null; then
    log_info "Status via Supervisor:"
    sudo supervisorctl status assessment 2>&1 | tee -a "$REPORT_FILE"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    log_info "Status via Systemd:"
    sudo systemctl status assessment --no-pager | tee -a "$REPORT_FILE"
fi
echo ""

# Teste de conectividade
log_section "11. TESTE DE ROTA (SIMULAÇÃO)"
log_info "Tentando acessar /admin/grupos para verificar se a página carrega..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -L http://localhost:5000/admin/grupos 2>&1 || echo "ERRO")
if [ "$RESPONSE" = "200" ]; then
    log_success "Página /admin/grupos retorna 200 OK"
elif [ "$RESPONSE" = "302" ]; then
    log_warning "Página retorna 302 (redirect, provavelmente precisa login)"
else
    log_error "Página retorna código: $RESPONSE"
fi
echo ""

# Instruções para o usuário
log_section "12. PRÓXIMOS PASSOS - TESTE MANUAL NO NAVEGADOR"
cat << 'EOF' | tee -a "$REPORT_FILE"

INSTRUÇÕES PARA TESTE MANUAL:

1. Abra o navegador e acesse /admin/grupos
2. Abra o Console JavaScript (F12 → Console)
3. Clique no botão "Excluir" de qualquer grupo
4. Observe se aparece algum erro no console

POSSÍVEIS ERROS NO CONSOLE:

a) "confirmarExclusao is not defined"
   → A função JavaScript não está carregada
   → Verifique se o template tem a função no <script>

b) "Cannot read property 'value' of null"
   → O campo csrf_token não existe
   → Verifique se há <input type="hidden" name="csrf_token" ...>

c) "405 Method Not Allowed"
   → A rota existe mas não aceita POST
   → Verifique se @admin_bp.route tem methods=['POST']

d) "404 Not Found"
   → A rota não existe
   → Verifique se a rota está registrada corretamente

e) Nada acontece (sem erro)
   → Pode ser problema com aspas no onclick
   → Verifique se onclick usa aspas simples: onclick='...'

VERIFICAR NO CÓDIGO-FONTE DA PÁGINA (Ctrl+U):

1. Procure por "function confirmarExclusao"
   → Deve estar presente no <script>

2. Procure por onclick no botão Excluir
   → Deve ser: onclick='confirmarExclusao("nome_grupo", tipo_id)'
   → Verifique se o nome do grupo tem aspas duplas dentro

3. Procure por <input type="hidden" name="csrf_token"
   → Deve existir dentro de um <form> ou no final do body

COPIAR E COLAR NO CONSOLE DO NAVEGADOR (para testar manualmente):

// Verificar se a função existe
console.log(typeof confirmarExclusao);  // Deve retornar "function"

// Verificar CSRF token
console.log(document.querySelector('input[name="csrf_token"]'));  // Deve retornar um elemento

// Testar função manualmente (substitua 'teste' e 1 por valores reais)
confirmarExclusao('teste', 1);

EOF

# Verificar arquivos modificados
log_section "13. ARQUIVOS MODIFICADOS (não commitados)"
git status --porcelain | tee -a "$REPORT_FILE"
echo ""

# Comparar com versão do Git
log_section "14. COMPARAR routes/admin.py COM VERSÃO DO GIT"
log_info "Diferenças no arquivo routes/admin.py:"
git diff routes/admin.py | tee -a "$REPORT_FILE"
echo ""

log_section "15. COMPARAR templates/admin/grupos_lista.html COM VERSÃO DO GIT"
log_info "Diferenças no arquivo templates/admin/grupos_lista.html:"
git diff templates/admin/grupos_lista.html | tee -a "$REPORT_FILE"
echo ""

# Sumário
log_section "SUMÁRIO DO DIAGNÓSTICO"
echo "Relatório completo salvo em: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo ""
echo "ENVIE ESTE ARQUIVO PARA ANÁLISE:" | tee -a "$REPORT_FILE"
echo "  cat $REPORT_FILE" | tee -a "$REPORT_FILE"
echo ""
echo "OU copie o conteúdo e cole na conversa." | tee -a "$REPORT_FILE"
echo ""

log_section "FIM DO DIAGNÓSTICO"
echo -e "${GREEN}Relatório completo salvo em: $REPORT_FILE${NC}"
echo ""
echo "Para visualizar o relatório:"
echo "  cat $REPORT_FILE"
echo ""
echo "Para copiar para área de transferência (se tiver xclip):"
echo "  cat $REPORT_FILE | xclip -selection clipboard"
echo ""
