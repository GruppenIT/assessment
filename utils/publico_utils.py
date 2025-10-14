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
            1. Identifique APENAS os 1-2 principais gaps (respostas "Não" ou "Parcial")
            
            2. Forneça 1-2 ações prioritárias e práticas para melhorar
            
            3. Use linguagem direta e profissional
            
            4. SEJA CONCISO: máximo de 2-3 linhas
            
            **FORMATO DE SAÍDA:**
            Retorne apenas o texto da recomendação em um único parágrafo curto, sem título ou formatação markdown.
            """
            
            # Chamar OpenAI
            response = openai_assistant.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": f"Você é {openai_assistant.assistant_name}. Você gera recomendações CURTAS, práticas e diretas (máximo 2-3 linhas) para melhorias em assessments de maturidade organizacional."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=200,
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
