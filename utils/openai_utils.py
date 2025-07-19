"""
Utilitários para integração com OpenAI
"""

import json
import logging
from datetime import datetime
from openai import OpenAI
from models.parametro_sistema import ParametroSistema
from utils.timezone_utils import format_date_local, format_datetime_local
from app import db

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
        """Gera texto de introdução do projeto"""
        if not self.is_configured():
            return None
        
        try:
            prompt = f"""
            Gere um texto de introdução para o relatório de assessment seguindo exatamente as instruções fornecidas.
            
            Dados do projeto em JSON:
            {json.dumps(projeto_data, indent=2, ensure_ascii=False)}
            
            Requisitos:
            1. Primeiro parágrafo: Cliente, tipos de assessments, respondentes, período de resposta
            2. Segundo parágrafo: Informações gerais sobre o conteúdo do relatório
            3. Use formato profissional e técnico
            4. Mantenha o tom formal e objetivo
            
            Responda apenas com o texto gerado, sem explicações adicionais.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Você é o {self.assistant_name}. Gere textos técnicos para relatórios de assessment de maturidade organizacional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Erro ao gerar introdução do projeto: {e}")
            return None
    
    def gerar_analise_dominio(self, dominio_data):
        """Gera análise técnica de um domínio"""
        if not self.is_configured():
            return None
        
        try:
            prompt = f"""
            Gere uma análise técnica detalhada do domínio seguindo exatamente as instruções fornecidas.
            
            Dados do domínio em JSON:
            {json.dumps(dominio_data, indent=2, ensure_ascii=False)}
            
            Requisitos:
            1. Análise técnica da pontuação obtida
            2. Destaque dos pontos de atenção
            3. Visão crítica dos pontos fortes e fracos
            4. Impactos na maturidade organizacional
            5. Use formato profissional e técnico
            
            Responda apenas com o texto gerado, sem explicações adicionais.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Você é o {self.assistant_name}. Analise domínios de assessment com visão técnica e crítica."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Erro ao gerar análise do domínio: {e}")
            return None
    
    def gerar_consideracoes_finais(self, projeto_data):
        """Gera considerações finais do projeto"""
        if not self.is_configured():
            return None
        
        try:
            prompt = f"""
            Gere as considerações finais para o relatório de assessment seguindo exatamente as instruções fornecidas.
            
            Dados do projeto em JSON:
            {json.dumps(projeto_data, indent=2, ensure_ascii=False)}
            
            Requisitos:
            1. Introdução às considerações finais
            2. Análise geral de maturidade
            3. Conclusões e recomendações finais
            4. Próximos passos sugeridos
            5. Use formato profissional e técnico
            
            Responda apenas com o texto gerado, sem explicações adicionais.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Você é o {self.assistant_name}. Gere considerações finais técnicas para relatórios de assessment."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Erro ao gerar considerações finais: {e}")
            return None

def coletar_dados_projeto(projeto):
    """Coleta dados do projeto para enviar ao ChatGPT"""
    from models.resposta import Resposta
    from models.pergunta import Pergunta
    from models.dominio import Dominio
    from models.respondente import Respondente
    from models.assessment_version import AssessmentVersao
    from sqlalchemy import func, desc
    
    # Dados básicos do projeto
    projeto_data = {
        'nome_projeto': projeto.nome,
        'cliente': projeto.cliente.nome if projeto.cliente else 'Cliente não especificado',
        'data_criacao': format_date_local(projeto.data_criacao),
        'data_conclusao': format_date_local(projeto.data_conclusao) if projeto.data_conclusao else 'Em andamento',
        'tipos_assessment': [],
        'respondentes': [],
        'dominios': [],
        'estatisticas_gerais': {}
    }
    
    # Tipos de assessment
    if projeto.versao_assessment:
        projeto_data['tipos_assessment'].append({
            'nome': projeto.versao_assessment.assessment_tipo.nome,
            'descricao': projeto.versao_assessment.assessment_tipo.descricao
        })
    
    # Respondentes
    respondentes = Respondente.query.filter_by(cliente_id=projeto.cliente_id).all()
    for respondente in respondentes:
        projeto_data['respondentes'].append({
            'nome': respondente.nome,
            'email': respondente.email,
            'login': respondente.login
        })
    
    # Análise por domínio
    if projeto.versao_assessment:
        dominios = Dominio.query.filter_by(versao_assessment_id=projeto.versao_assessment_id).all()
        
        for dominio in dominios:
            # Estatísticas do domínio
            respostas_dominio = Resposta.query.join(Pergunta).filter(
                Pergunta.dominio_id == dominio.id,
                Resposta.projeto_id == projeto.id
            ).all()
            
            if respostas_dominio:
                pontuacoes = [r.pontuacao for r in respostas_dominio if r.pontuacao is not None]
                comentarios = [r.comentario for r in respostas_dominio if r.comentario and r.comentario.strip()]
                
                dominio_data = {
                    'nome': dominio.nome,
                    'descricao': dominio.descricao,
                    'total_perguntas': len(respostas_dominio),
                    'pontuacao_media': sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0,
                    'pontuacao_maxima': max(pontuacoes) if pontuacoes else 0,
                    'pontuacao_minima': min(pontuacoes) if pontuacoes else 0,
                    'total_comentarios': len(comentarios),
                    'comentarios_destaque': comentarios[:5],  # Primeiros 5 comentários
                    'perguntas_criticas': []
                }
                
                # Perguntas com pontuação baixa (críticas)
                for resposta in respostas_dominio:
                    if resposta.pontuacao is not None and resposta.pontuacao <= 2:
                        dominio_data['perguntas_criticas'].append({
                            'pergunta': resposta.pergunta.texto,
                            'pontuacao': resposta.pontuacao,
                            'comentario': resposta.comentario or ''
                        })
                
                projeto_data['dominios'].append(dominio_data)
    
    # Estatísticas gerais
    total_respostas = Resposta.query.filter_by(projeto_id=projeto.id).count()
    respostas_com_pontuacao = Resposta.query.filter(
        Resposta.projeto_id == projeto.id,
        Resposta.pontuacao.isnot(None)
    ).all()
    
    if respostas_com_pontuacao:
        pontuacoes_gerais = [r.pontuacao for r in respostas_com_pontuacao]
        projeto_data['estatisticas_gerais'] = {
            'total_respostas': total_respostas,
            'pontuacao_media_geral': sum(pontuacoes_gerais) / len(pontuacoes_gerais),
            'total_dominios': len(projeto_data['dominios']),
            'total_respondentes': len(projeto_data['respondentes'])
        }
    
    return projeto_data

def gerar_relatorio_ia(projeto):
    """Gera relatório completo usando IA"""
    assistant = OpenAIAssistant()
    
    if not assistant.is_configured():
        return {
            'erro': 'Integração com ChatGPT não configurada. Configure a API Key e o nome do Assistant em Parâmetros do Sistema.'
        }
    
    try:
        # Coletar dados do projeto
        projeto_data = coletar_dados_projeto(projeto)
        
        # Gerar introdução
        introducao = assistant.gerar_introducao_projeto(projeto_data)
        
        # Gerar análise de cada domínio
        analises_dominios = []
        for dominio_data in projeto_data['dominios']:
            analise = assistant.gerar_analise_dominio(dominio_data)
            if analise:
                analises_dominios.append({
                    'dominio': dominio_data['nome'],
                    'analise': analise
                })
        
        # Gerar considerações finais
        consideracoes_finais = assistant.gerar_consideracoes_finais(projeto_data)
        
        return {
            'introducao': introducao,
            'analises_dominios': analises_dominios,
            'consideracoes_finais': consideracoes_finais,
            'assistant_name': assistant.assistant_name,
            'gerado_em': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Erro ao gerar relatório IA: {e}")
        return {
            'erro': f'Erro ao gerar relatório: {str(e)}'
        }