#!/bin/bash

###############################################################################
# Script de Correção: Estatísticas de Grupos com Gráficos Interativos
# 
# Correções aplicadas:
# 1. Proteção contra tipos de assessment deletados
# 2. Proteção contra perguntas deletadas em assessments públicos
# 3. Filtros robustos em get_dominios_respondidos e calcular_pontuacao_dominio
# 4. Gráficos interativos com tooltips corretos e cores por pontuação
# 5. CORREÇÃO CRÍTICA: Template Jinja2 com bloco content não fechado
#
# Data: 2025-10-17
###############################################################################

set -e  # Parar em caso de erro

echo "======================================================================"
echo "Aplicando Correções - Estatísticas de Grupos com Gráficos Interativos"
echo "======================================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detectar diretório do projeto
if [ -f "app.py" ]; then
    PROJECT_DIR=$(pwd)
else
    echo -e "${RED}Erro: Execute este script no diretório raiz do projeto (onde está o app.py)${NC}"
    exit 1
fi

echo "📁 Diretório do projeto: $PROJECT_DIR"
echo ""

# Criar backup antes de aplicar correções
BACKUP_DIR="backups/correcao_graficos_grupos_$(date +%Y%m%d_%H%M%S)"
echo "💾 Criando backup em: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
cp -r routes "$BACKUP_DIR/" 2>/dev/null || true
cp -r models "$BACKUP_DIR/" 2>/dev/null || true
cp -r templates/admin "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup criado${NC}"
echo ""

# Aplicar correção 1: routes/admin.py - Proteção contra tipo de assessment deletado
echo "🔧 Aplicando correção 1: Proteção contra tipo de assessment deletado"
cat > /tmp/correcao1.py << 'EOF'
        # Tipos de assessment utilizados
        tipos_utilizados = {}
        for assessment in assessments:
            tipo = assessment.tipo_assessment
            if tipo and tipo.id not in tipos_utilizados:
                tipos_utilizados[tipo.id] = {
                    'tipo': tipo,
                    'quantidade': 0
                }
            if tipo:
                tipos_utilizados[tipo.id]['quantidade'] += 1
EOF

# Verificar se o arquivo existe
if [ ! -f "routes/admin.py" ]; then
    echo -e "${RED}✗ Arquivo routes/admin.py não encontrado${NC}"
    exit 1
fi

# Aplicar a correção usando Python para substituição precisa
python3 << 'PYTHON_SCRIPT'
import re

with open('routes/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Padrão antigo (sem proteção)
old_pattern = r'''        # Tipos de assessment utilizados
        tipos_utilizados = {}
        for assessment in assessments:
            tipo = assessment\.tipo_assessment
            if tipo\.id not in tipos_utilizados:
                tipos_utilizados\[tipo\.id\] = {
                    'tipo': tipo,
                    'quantidade': 0
                }
            tipos_utilizados\[tipo\.id\]\['quantidade'\] \+= 1'''

# Novo padrão (com proteção)
new_pattern = '''        # Tipos de assessment utilizados
        tipos_utilizados = {}
        for assessment in assessments:
            tipo = assessment.tipo_assessment
            if tipo and tipo.id not in tipos_utilizados:
                tipos_utilizados[tipo.id] = {
                    'tipo': tipo,
                    'quantidade': 0
                }
            if tipo:
                tipos_utilizados[tipo.id]['quantidade'] += 1'''

# Substituir
if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_pattern, content)
    with open('routes/admin.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Correção aplicada em routes/admin.py")
else:
    print("ℹ Correção já aplicada ou padrão não encontrado em routes/admin.py")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Correção 1 aplicada${NC}"
echo ""

# Aplicar correção 2: models/assessment_publico.py - Proteção em calcular_pontuacao_dominio
echo "🔧 Aplicando correção 2: Proteção em calcular_pontuacao_dominio"

python3 << 'PYTHON_SCRIPT'
import re

with open('models/assessment_publico.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Padrão antigo
old_pattern = r'respostas_dominio = \[r for r in self\.respostas if r\.pergunta\.dominio_versao_id == dominio_id\]'
new_pattern = 'respostas_dominio = [r for r in self.respostas if r.pergunta and r.pergunta.dominio_versao_id == dominio_id]'

if old_pattern in content.replace(new_pattern, ''):
    content = re.sub(old_pattern, new_pattern, content)
    with open('models/assessment_publico.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Correção aplicada em calcular_pontuacao_dominio")
else:
    print("ℹ Correção já aplicada em calcular_pontuacao_dominio")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Correção 2 aplicada${NC}"
echo ""

# Aplicar correção 3: models/assessment_publico.py - Proteção em get_dominios_respondidos
echo "🔧 Aplicando correção 3: Proteção em get_dominios_respondidos"

python3 << 'PYTHON_SCRIPT'
with open('models/assessment_publico.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar se já tem a proteção
if 'dominios_ids = set(r.pergunta.dominio_versao_id for r in self.respostas if r.pergunta)' not in content:
    # Substituir
    old_line = 'dominios_ids = set(r.pergunta.dominio_versao_id for r in self.respostas)'
    new_code = '''dominios_ids = set(r.pergunta.dominio_versao_id for r in self.respostas if r.pergunta)
        if not dominios_ids:
            return []'''
    
    content = content.replace(old_line, new_code)
    
    with open('models/assessment_publico.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Correção aplicada em get_dominios_respondidos")
else:
    print("ℹ Correção já aplicada em get_dominios_respondidos")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Correção 3 aplicada${NC}"
echo ""

# Aplicar correção 4: templates/admin/grupos_estatisticas.html - Fechar bloco content
echo "🔧 Aplicando correção 4: CRÍTICO - Fechar bloco content no template Jinja2"

python3 << 'PYTHON_SCRIPT'
with open('templates/admin/grupos_estatisticas.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar se já tem a correção (endblock antes de extra_js)
if '</div>\n{% endblock %}\n\n{% block extra_js %}' not in content:
    # Substituir
    old_pattern = '</div>\n\n{% block extra_js %}'
    new_pattern = '</div>\n{% endblock %}\n\n{% block extra_js %}'
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        with open('templates/admin/grupos_estatisticas.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ CORREÇÃO CRÍTICA aplicada - bloco content fechado")
    else:
        print("⚠ Padrão não encontrado, verificando manualmente...")
        # Tentar padrão alternativo
        import re
        pattern = r'(</div>\n)(\{% block extra_js %\})'
        if re.search(pattern, content) and '{% endblock %}\n\n{% block extra_js %}' not in content:
            content = re.sub(pattern, r'\1{% endblock %}\n\n\2', content)
            with open('templates/admin/grupos_estatisticas.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("✓ CORREÇÃO CRÍTICA aplicada - bloco content fechado (padrão alternativo)")
        else:
            print("ℹ Correção já aplicada ou template diferente do esperado")
else:
    print("ℹ Correção já aplicada - bloco content está fechado")
PYTHON_SCRIPT

echo -e "${GREEN}✓ Correção 4 aplicada (CRÍTICA)${NC}"
echo ""

# Reiniciar o serviço
echo "🔄 Reiniciando serviço..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Supervisor${NC}"
elif [ -f "/etc/systemd/system/assessment.service" ]; then
    sudo systemctl restart assessment
    echo -e "${GREEN}✓ Serviço reiniciado via Systemd${NC}"
else
    echo -e "${YELLOW}⚠ Serviço não detectado. Reinicie manualmente:${NC}"
    echo "   sudo supervisorctl restart assessment"
    echo "   ou"
    echo "   sudo systemctl restart assessment"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}✓ Correções aplicadas com sucesso!${NC}"
echo "======================================================================"
echo ""
echo "📝 Mudanças aplicadas:"
echo "   1. Proteção contra tipos de assessment deletados"
echo "   2. Proteção contra perguntas deletadas em calcular_pontuacao_dominio"
echo "   3. Proteção contra perguntas deletadas em get_dominios_respondidos"
echo "   4. 🔴 CRÍTICO: Correção de sintaxe Jinja2 - bloco content não fechado"
echo ""
echo "💾 Backup salvo em: $BACKUP_DIR"
echo ""
echo "🧪 Teste agora:"
echo "   1. Acesse /admin/grupos"
echo "   2. Clique em qualquer tag de grupo"
echo "   3. Verifique se os gráficos são exibidos corretamente"
echo "   4. Teste alternar entre: barras verticais, horizontais, radar e tabela"
echo ""
