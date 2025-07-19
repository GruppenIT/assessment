"""
Utilitários para integração com OpenAI
"""

import json
import logging
from datetime import datetime
from openai import OpenAI
from models.parametro_sistema import ParametroSistema
from utils.timezone_utils import format_date_local, format_datetime_local

class OpenAIAssistant:
    """Classe para gerenciar a integração com OpenAI Assistant"""
    
    def __init__(self):
        self.client = None
        self.assistant_name = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa o cliente OpenAI"""
        try:
            config = ParametroSistema.get_openai_config()
            api_key = config.get('api_key')
            self.assistant_name = config.get('assistant_name', 'Assessment Assistant')
            
            if api_key:
                self.client = OpenAI(api_key=api_key)
                logging.info(f"Cliente OpenAI inicializado com assistant: {self.assistant_name}")
            else:
                logging.warning("API Key OpenAI não configurada")
        except Exception as e:
            logging.error(f"Erro ao inicializar cliente OpenAI: {e}")
    
    def is_configured(self):
        """Verifica se o cliente está configurado"""
        return self.client is not None
    
    def gerar_introducao_projeto(self, projeto_data):
        """Gera texto de introdução do projeto usando as instruções do assistente"""
        if not self.is_configured():
            return None
        
        try:
            # Preparar prompt com as instruções específicas
            prompt = f"""
            Siga exatamente as instruções para gerar a introdução do relatório de assessment:

            **DADOS DO PROJETO (JSON):**
            {json.dumps(projeto_data, indent=2, ensure_ascii=False)}

            **INSTRUÇÕES:**
            1. Primeiro Parágrafo:
               - Cliente: Nome do cliente
               - Tipo de Assessments: Descrição dos tipos de assessments utilizados no projeto
               - Respondentes: Nome do(s) respondente(s) com e-mail entre parênteses
               - Período de Resposta: Data de início e término da coleta de respostas

            2. Segundo Parágrafo:
               - Informações gerais sobre o conteúdo do relatório: mencione que o relatório inclui estatísticas, memorial detalhado de respostas com recomendações de melhoria de postura e considerações finais.

            **FORMATO DE SAÍDA:**
            Retorne apenas o texto da introdução, sem explicações adicionais ou formatação markdown.
            Use linguagem técnica e profissional.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": f"Você é o {self.assistant_name}. Gere textos técnicos para relatórios de assessment de maturidade organizacional seguindo exatamente as instruções fornecidas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Erro ao gerar introdução do projeto: {e}")
            return None

def coletar_dados_projeto_para_ia(projeto):
    """Coleta dados do projeto para envio à IA"""
    try:
        # Dados básicos do projeto
        dados = {
            "projeto": {
                "nome": projeto.nome,
                "data_criacao": format_date_local(projeto.data_criacao) if projeto.data_criacao else None,
                "data_finalizacao": format_date_local(projeto.data_finalizacao) if projeto.data_finalizacao else None
            },
            "cliente": {
                "nome": projeto.cliente.nome if projeto.cliente else "Cliente não especificado"
            },
            "respondentes": [],
            "tipos_assessment": []
        }
        
        # Coletar respondentes
        respondentes_ativos = projeto.get_respondentes_ativos()
        for respondente in respondentes_ativos:
            dados["respondentes"].append({
                "nome": respondente.nome,
                "email": respondente.email
            })
        
        # Coletar tipos de assessment
        tipos = projeto.get_tipos_assessment()
        for tipo in tipos:
            dados["tipos_assessment"].append({
                "nome": tipo.nome,
                "descricao": tipo.descricao
            })
        
        return dados
        
    except Exception as e:
        logging.error(f"Erro ao coletar dados do projeto para IA: {e}")
        return None

def gerar_introducao_ia(projeto):
    """Função principal para gerar introdução com IA"""
    try:
        # Verificar se projeto está finalizado
        if not projeto.is_totalmente_finalizado():
            return {
                'erro': 'O projeto deve estar totalmente finalizado para gerar a introdução.'
            }
        
        # Coletar dados do projeto
        dados_projeto = coletar_dados_projeto_para_ia(projeto)
        if not dados_projeto:
            return {
                'erro': 'Erro ao coletar dados do projeto.'
            }
        
        # Inicializar assistente
        assistant = OpenAIAssistant()
        if not assistant.is_configured():
            return {
                'erro': 'Integração com ChatGPT não configurada. Configure a API Key e o nome do Assistant em Parâmetros do Sistema.'
            }
        
        # Gerar introdução
        introducao = assistant.gerar_introducao_projeto(dados_projeto)
        if not introducao:
            return {
                'erro': 'Erro ao gerar texto da introdução.'
            }
        
        return {
            'introducao': introducao,
            'assistant_name': assistant.assistant_name,
            'gerado_em': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erro ao gerar introdução IA: {e}")
        return {
            'erro': f'Erro interno: {str(e)}'
        }