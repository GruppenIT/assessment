"""
Utilitários para integração com OpenAI
"""

import os
import json
import logging
from datetime import datetime

def melhorar_texto_com_orientacao(texto_atual, orientacao, tipo_texto, projeto):
    """
    Melhora um texto existente usando GPT com orientações específicas do usuário
    
    Args:
        texto_atual: Texto atual a ser melhorado
        orientacao: Orientações do usuário para melhoria
        tipo_texto: 'introducao' ou 'consideracoes'
        projeto: Objeto do projeto para contexto
    
    Returns:
        str: Texto melhorado ou None se erro
    """
    try:
        # Verificar se OpenAI está configurado através dos parâmetros do sistema
        from models.parametro_sistema import ParametroSistema
        
        openai_config = ParametroSistema.get_openai_config()
        if not openai_config or not openai_config.get('api_key'):
            logging.error("OpenAI API Key não configurada nos parâmetros do sistema")
            return None
        
        from openai import OpenAI
        client = OpenAI(api_key=openai_config['api_key'])
        
        # Preparar contexto do projeto
        contexto_projeto = f"""
        Projeto: {projeto.nome}
        Cliente: {projeto.cliente.nome}
        Tipo de Empresa: {projeto.cliente.tipo_empresa or 'Não especificado'}
        Segmento: {projeto.cliente.segmento or 'Não especificado'}
        Localidade: {projeto.cliente.localidade or 'Não especificado'}
        """
        
        # Definir prompt específico para cada tipo
        if tipo_texto == 'introducao':
            prompt_sistema = """Você é um consultor especialista em cibersegurança que escreve introduções para relatórios de assessment de maturidade em cibersegurança. 

Sua tarefa é MELHORAR o texto de introdução já existente, seguindo as orientações específicas do usuário.

Características da introdução ideal:
- Profissional e técnica, mas acessível
- Contextualiza o assessment de cibersegurança
- Menciona o cliente de forma apropriada
- Explica brevemente a metodologia utilizada
- Define expectativas sobre os resultados

Mantenha o tom formal e especializado, mas compreensível para executivos."""

            prompt_usuario = f"""CONTEXTO DO PROJETO:
{contexto_projeto}

TEXTO ATUAL DA INTRODUÇÃO:
{texto_atual}

ORIENTAÇÕES PARA MELHORIA:
{orientacao}

Por favor, melhore o texto da introdução seguindo exatamente as orientações fornecidas. Mantenha a estrutura profissional e retorne apenas o texto melhorado, sem comentários adicionais."""

        else:  # consideracoes
            prompt_sistema = """Você é um consultor especialista em cibersegurança que escreve considerações finais para relatórios de assessment de maturidade.

Sua tarefa é MELHORAR o texto das considerações finais já existente, seguindo as orientações específicas do usuário.

Características das considerações finais ideais:
- Resumem os principais achados
- Fornecem recomendações estratégicas
- Destacam prioridades de implementação
- Incluem perspectivas de evolução da maturidade
- Tom consultivo e direcionador

Mantenha o foco em insights acionáveis e recomendações práticas."""

            prompt_usuario = f"""CONTEXTO DO PROJETO:
{contexto_projeto}

TEXTO ATUAL DAS CONSIDERAÇÕES FINAIS:
{texto_atual}

ORIENTAÇÕES PARA MELHORIA:
{orientacao}

Por favor, melhore o texto das considerações finais seguindo exatamente as orientações fornecidas. Mantenha o tom consultivo e retorne apenas o texto melhorado, sem comentários adicionais."""

        # Fazer chamada para OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # Usar o modelo mais recente
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        
        texto_melhorado = response.choices[0].message.content
        if texto_melhorado:
            texto_melhorado = texto_melhorado.strip()
        
        if not texto_melhorado:
            logging.error("OpenAI retornou texto vazio")
            return None
            
        # Para considerações finais, manter formato JSON se o original era JSON
        if tipo_texto == 'consideracoes':
            try:
                # Verificar se texto original era JSON
                json.loads(projeto.consideracoes_finais_ia)
                
                # Se era JSON, manter estrutura JSON
                consideracoes_json = {
                    "consideracoes": texto_melhorado,
                    "assistant_name": f"{openai_config.get('assistant_name', 'ChatGPT')} (GPT-4o) - Melhorado com orientações",
                    "gerado_em": datetime.utcnow().isoformat(),
                    "dados_utilizados": {
                        "total_assessments": len(projeto.assessments),
                        "total_respostas": len(projeto.respostas)
                    },
                    "tipo_melhoria": "orientacao_personalizada",
                    "orientacao_aplicada": orientacao
                }
                
                return json.dumps(consideracoes_json, ensure_ascii=False, indent=2)
                
            except (json.JSONDecodeError, TypeError):
                # Se não era JSON, retornar texto simples
                pass
        
        return texto_melhorado
        
    except Exception as e:
        logging.error(f"Erro ao melhorar texto com OpenAI: {e}")
        return None