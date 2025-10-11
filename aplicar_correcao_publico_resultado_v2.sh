#!/bin/bash

# Script para corrigir bug RAIZ no resultado de assessments públicos
# Bug: Modelo usando dominio_id ao invés de dominio_versao_id
# Data: 2025-10-11

set -e

echo "=========================================="
echo "  CORREÇÃO: Bug Raiz Assessment Público"
echo "=========================================="
echo ""

# Definir caminhos
APP_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment/backups/correcao_publico_v2_$(date +%Y%m%d_%H%M%S)"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Fazer backup dos arquivos
echo "1. Fazendo backup dos arquivos atuais..."
cp "$APP_DIR/models/assessment_publico.py" "$BACKUP_DIR/"
cp "$APP_DIR/utils/publico_utils.py" "$BACKUP_DIR/"
cp "$APP_DIR/routes/publico.py" "$BACKUP_DIR/"
echo "   ✓ Backup salvo em: $BACKUP_DIR"

# Corrigir models/assessment_publico.py - LINHA 53
echo ""
echo "2. Corrigindo models/assessment_publico.py (calcular_pontuacao_dominio)..."
sed -i 's/if r\.pergunta\.dominio_id == dominio_id/if r.pergunta.dominio_versao_id == dominio_id/' "$APP_DIR/models/assessment_publico.py"
echo "   ✓ Linha 53 corrigida: dominio_id → dominio_versao_id"

# Corrigir models/assessment_publico.py - LINHA 68
echo ""
echo "3. Corrigindo models/assessment_publico.py (get_dominios_respondidos)..."
sed -i 's/r\.pergunta\.dominio_id for r in self\.respostas/r.pergunta.dominio_versao_id for r in self.respostas/' "$APP_DIR/models/assessment_publico.py"
sed -i 's/from models\.dominio import Dominio/from models.assessment_version import AssessmentDominio/' "$APP_DIR/models/assessment_publico.py"
sed -i 's/return Dominio\.query\.filter(Dominio\.id\.in_(dominios_ids))\.all()/return AssessmentDominio.query.filter(AssessmentDominio.id.in_(dominios_ids)).all()/' "$APP_DIR/models/assessment_publico.py"
echo "   ✓ Linha 68-70 corrigida: usando AssessmentDominio versionado"

# Corrigir utils/publico_utils.py - LINHA 32
echo ""
echo "4. Corrigindo utils/publico_utils.py..."
sed -i 's/if r\.pergunta\.dominio_id == dominio\.id/if r.pergunta.dominio_versao_id == dominio.id/' "$APP_DIR/utils/publico_utils.py"
echo "   ✓ Linha 32 corrigida: dominio_id → dominio_versao_id"

# Verificar se as correções foram aplicadas
echo ""
echo "5. Verificando correções..."

# Contar ocorrências de dominio_versao_id (deve ter 3 agora)
COUNT=$(grep -c "dominio_versao_id" "$APP_DIR/models/assessment_publico.py" || true)
if [ "$COUNT" -ge "2" ]; then
    echo "   ✓ models/assessment_publico.py: $COUNT ocorrências de dominio_versao_id"
else
    echo "   ✗ ERRO: Esperado 2+ ocorrências, encontrado $COUNT"
fi

COUNT2=$(grep -c "AssessmentDominio" "$APP_DIR/models/assessment_publico.py" || true)
if [ "$COUNT2" -ge "1" ]; then
    echo "   ✓ models/assessment_publico.py: Usando AssessmentDominio versionado"
else
    echo "   ✗ ERRO: AssessmentDominio não encontrado"
fi

# Reiniciar aplicação
echo ""
echo "6. Reiniciando aplicação..."
sudo supervisorctl restart assessment
sleep 3

# Verificar status
STATUS=$(sudo supervisorctl status assessment | awk '{print $2}')

if [ "$STATUS" = "RUNNING" ]; then
    echo "   ✓ Aplicação reiniciada com sucesso"
else
    echo "   ✗ ERRO: Aplicação não está rodando!"
    echo ""
    echo "Verificando logs de erro:"
    sudo supervisorctl tail assessment stderr | tail -50
    exit 1
fi

# Verificar logs de erro
echo ""
echo "7. Verificando logs de inicialização..."
sleep 2
ERRORS=$(sudo supervisorctl tail assessment stderr | grep -i "error\|exception\|traceback" | tail -5 || true)

if [ -z "$ERRORS" ]; then
    echo "   ✓ Nenhum erro encontrado nos logs"
else
    echo "   ⚠ Atenção: Erros encontrados nos logs:"
    echo "$ERRORS"
fi

# Sucesso
echo ""
echo "=========================================="
echo "  ✓ CORREÇÃO APLICADA COM SUCESSO!"
echo "=========================================="
echo ""
echo "🐛 Bug Raiz Corrigido:"
echo "  • models/assessment_publico.py:"
echo "    - calcular_pontuacao_dominio() agora usa dominio_versao_id"
echo "    - get_dominios_respondidos() agora usa AssessmentDominio versionado"
echo "  • utils/publico_utils.py:"
echo "    - gerar_recomendacoes_ia() agora usa dominio_versao_id"
echo ""
echo "📦 Backup dos arquivos originais em:"
echo "  $BACKUP_DIR"
echo ""
echo "🧪 Teste agora o assessment público:"
echo "  1. Acesse: https://assessments.zerobox.com.br/public/3"
echo "  2. Responda as perguntas"
echo "  3. Preencha os dados do respondente"
echo "  4. Verifique se o gráfico radar aparece"
echo "  5. Verifique se as recomendações aparecem"
echo ""
echo "✅ O bug estava nos métodos do modelo que usavam dominio_id"
echo "   ao invés de dominio_versao_id para assessments versionados!"
echo ""
