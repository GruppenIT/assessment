#!/bin/bash

# Script para corrigir bug no resultado de assessments públicos
# Bug: Gráfico radar e recomendações em branco
# Data: 2025-10-11

set -e

echo "=========================================="
echo "  CORREÇÃO: Resultado Assessment Público"
echo "=========================================="
echo ""

# Definir caminhos
APP_DIR="/var/www/assessment"
BACKUP_DIR="/var/www/assessment/backups/correcao_publico_$(date +%Y%m%d_%H%M%S)"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Fazer backup dos arquivos
echo "1. Fazendo backup dos arquivos atuais..."
cp "$APP_DIR/routes/publico.py" "$BACKUP_DIR/"
cp "$APP_DIR/utils/publico_utils.py" "$BACKUP_DIR/"
echo "   ✓ Backup salvo em: $BACKUP_DIR"

# Corrigir utils/publico_utils.py
echo ""
echo "2. Corrigindo utils/publico_utils.py..."
cat > "$APP_DIR/utils/publico_utils.py" << 'EOF'
import logging
from utils.openai_utils import OpenAIAssistant
import json

def gerar_recomendacoes_ia(assessment_publico, dominios_dados):
    """
    Gera recomendações de melhoria para cada domínio usando OpenAI
    
    Args:
        assessment_publico: Objeto AssessmentPublico
        dominios_dados: Lista de dicionários com domínio e pontuação
        
    Returns:
        Lista de recomendações (strings) para cada domínio
    """
    openai_assistant = OpenAIAssistant()
    
    if not openai_assistant.is_configured():
        logging.warning("OpenAI não configurado para gerar recomendações públicas")
        return []
    
    recomendacoes = []
    
    for dominio_data in dominios_dados:
        try:
            dominio = dominio_data['dominio']
            pontuacao = dominio_data['pontuacao']
            
            # Obter respostas do domínio (usando dominio_versao_id para assessments versionados)
            respostas_dominio = [
                r for r in assessment_publico.respostas 
                if r.pergunta.dominio_versao_id == dominio.id
            ]
            
            # Preparar dados para análise
            perguntas_respostas = []
            for resposta in respostas_dominio:
                perguntas_respostas.append({
                    'pergunta': resposta.pergunta.texto,
                    'resposta': resposta.get_texto_resposta(),
                    'valor': resposta.valor
                })
            
            # Criar prompt para OpenAI
            prompt = f"""
            Como consultor especializado em assessments de maturidade organizacional, analise as respostas do domínio "{dominio.nome}" e forneça recomendações práticas de melhoria.

            **DADOS DO DOMÍNIO:**
            - Nome: {dominio.nome}
            - Descrição: {dominio.descricao or 'Não informada'}
            - Pontuação obtida: {pontuacao}%
            
            **RESPOSTAS DO DOMÍNIO:**
            {json.dumps(perguntas_respostas, indent=2, ensure_ascii=False)}
            
            **INSTRUÇÕES PARA RECOMENDAÇÃO:**
            1. Analise as respostas considerando:
               - Respostas "Não" (valor 0) indicam ausência total da prática
               - Respostas "Parcial" (valor 3) indicam implementação parcial
               - Respostas "Sim" (valor 5) indicam implementação completa
            
            2. Identifique os principais gaps (respostas "Não" e "Parcial")
            
            3. Forneça 2-3 recomendações práticas e objetivas focadas em:
               - Priorizar ações para as áreas com resposta "Não"
               - Melhorar áreas com resposta "Parcial"
               - Fortalecer processos já implementados
            
            4. Use linguagem direta e profissional
            
            5. Estruture a resposta em um único parágrafo de 4-6 linhas
            
            **FORMATO DE SAÍDA:**
            Retorne apenas o texto da recomendação, sem título ou formatação markdown.
            """
            
            # Chamar OpenAI
            response = openai_assistant.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": f"Você é {openai_assistant.assistant_name}. Você gera recomendações práticas e diretas para melhorias em assessments de maturidade organizacional."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            recomendacao = response.choices[0].message.content.strip()
            recomendacoes.append(recomendacao)
            
            logging.info(f"Recomendação gerada para domínio {dominio.nome}")
            
        except Exception as e:
            logging.error(f"Erro ao gerar recomendação para domínio {dominio.nome}: {e}")
            # Adicionar recomendação padrão em caso de erro
            recomendacoes.append(
                f"Com base na pontuação de {pontuacao}%, recomenda-se revisar e fortalecer "
                f"as práticas relacionadas a {dominio.nome}, priorizando a implementação "
                f"de processos formais e a melhoria contínua dos controles existentes."
            )
    
    return recomendacoes


def calcular_nivel_maturidade(pontuacao):
    """
    Calcula o nível de maturidade com base na pontuação
    
    Args:
        pontuacao: Pontuação de 0 a 100
        
    Returns:
        Tupla (nivel_texto, cor_css)
    """
    if pontuacao >= 80:
        return ('Otimizado', 'success')
    elif pontuacao >= 60:
        return ('Gerenciado', 'primary')
    elif pontuacao >= 40:
        return ('Definido', 'info')
    elif pontuacao >= 20:
        return ('Em Desenvolvimento', 'warning')
    else:
        return ('Inicial', 'danger')
EOF

echo "   ✓ Arquivo utils/publico_utils.py corrigido"

# Corrigir a parte relevante do routes/publico.py
echo ""
echo "3. Corrigindo routes/publico.py..."

# Usar sed para substituir o bloco de código específico
sed -i.bak '/# Gerar recomendações com OpenAI/,/session.pop(session_key, None)/c\
    # Gerar recomendações com OpenAI\
    from utils.publico_utils import gerar_recomendacoes_ia\
    \
    try:\
        logging.info(f"Gerando recomendações IA para assessment público {assessment_publico.id}")\
        recomendacoes = gerar_recomendacoes_ia(assessment_publico, dominios_dados)\
        \
        # Atualizar recomendações nos dados dos domínios\
        for i, dominio_data in enumerate(dominios_dados):\
            if i < len(recomendacoes):\
                dominio_data["recomendacao"] = recomendacoes[i]\
                logging.info(f"Recomendação atribuída ao domínio {dominio_data[\"dominio\"].nome}")\
    except Exception as e:\
        logging.error(f"Erro ao gerar recomendações IA: {e}", exc_info=True)\
        # Se falhar, adicionar recomendações padrão\
        for dominio_data in dominios_dados:\
            pontuacao = dominio_data["pontuacao"]\
            dominio_nome = dominio_data["dominio"].nome\
            dominio_data["recomendacao"] = (\
                f"Com base na pontuação de {pontuacao:.0f}%, recomenda-se revisar e fortalecer "\
                f"as práticas relacionadas a {dominio_nome}, priorizando a implementação "\
                f"de processos formais e a melhoria contínua dos controles existentes."\
            )\
    \
    # Limpar sessão\
    session_key = f"assessment_publico_{assessment_id}"\
    session.pop(session_key, None)' "$APP_DIR/routes/publico.py"

echo "   ✓ Arquivo routes/publico.py corrigido"

# Reiniciar aplicação
echo ""
echo "4. Reiniciando aplicação..."
sudo supervisorctl restart assessment
sleep 2

# Verificar status
STATUS=$(sudo supervisorctl status assessment | awk '{print $2}')

if [ "$STATUS" = "RUNNING" ]; then
    echo "   ✓ Aplicação reiniciada com sucesso"
else
    echo "   ✗ ERRO: Aplicação não está rodando!"
    echo ""
    echo "Verificando logs de erro:"
    sudo supervisorctl tail assessment stderr
    exit 1
fi

# Sucesso
echo ""
echo "=========================================="
echo "  ✓ CORREÇÃO APLICADA COM SUCESSO!"
echo "=========================================="
echo ""
echo "Mudanças aplicadas:"
echo "  • Corrigido filtro de respostas (dominio_versao_id)"
echo "  • Adicionadas recomendações padrão para fallback"
echo "  • Melhorado logging para debug"
echo ""
echo "Backup dos arquivos originais em:"
echo "  $BACKUP_DIR"
echo ""
echo "Agora teste novamente o assessment público:"
echo "  https://assessments.zerobox.com.br/public/1"
echo "  https://assessments.zerobox.com.br/public/3"
echo ""
