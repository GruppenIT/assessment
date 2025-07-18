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
        
    def _make_request_with_retry(self, request_func, max_retries=3, timeout=60):
        """Executa requisição com retry e timeout"""
        import time
        
        for attempt in range(max_retries):
            try:
                return request_func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logging.warning(f"Tentativa {attempt + 1} falhou: {e}. Tentando novamente...")
                time.sleep(2 ** attempt)  # Backoff exponencial
        
        return None
    
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
        config = ParametroSistema.get_openai_config()
        return self.client is not None and config.get('api_key_configured', False)
    
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
            
            def make_request():
                return self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"Você é o {self.assistant_name}. Gere textos técnicos para relatórios de assessment de maturidade organizacional."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                    timeout=30
                )
            
            response = self._make_request_with_retry(make_request)
            
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
            
            def make_request():
                return self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"Você é o {self.assistant_name}. Analise domínios de assessment com visão técnica e crítica."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7,
                    timeout=30
                )
            
            response = self._make_request_with_retry(make_request)
            
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
            
            def make_request():
                return self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"Você é o {self.assistant_name}. Gere considerações finais técnicas para relatórios de assessment."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.7,
                    timeout=30
                )
            
            response = self._make_request_with_retry(make_request)
            
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
    
    def format_date_local(date_obj):
        """Formata data para display local"""
        if date_obj:
            return date_obj.strftime('%d/%m/%Y')
        return None
    
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
    for projeto_assessment in projeto.assessments:
        if projeto_assessment.versao_assessment:
            projeto_data['tipos_assessment'].append({
                'nome': projeto_assessment.versao_assessment.tipo.nome,
                'descricao': projeto_assessment.versao_assessment.tipo.descricao
            })
        elif projeto_assessment.tipo_assessment:
            projeto_data['tipos_assessment'].append({
                'nome': projeto_assessment.tipo_assessment.nome,
                'descricao': projeto_assessment.tipo_assessment.descricao
            })
    
    # Respondentes
    try:
        respondentes = projeto.get_respondentes_ativos()
        for respondente in respondentes:
            projeto_data['respondentes'].append({
                'nome': respondente.nome,
                'email': respondente.email,
                'login': respondente.login
            })
    except Exception as e:
        logging.warning(f"Erro ao carregar respondentes: {e}")
        projeto_data['respondentes'] = []
    
    # Análise por domínio
    try:
        for projeto_assessment in projeto.assessments:
            if projeto_assessment.versao_assessment_id:
                # Novo sistema de versionamento
                from models.assessment_version import AssessmentDominio
                dominios = AssessmentDominio.query.filter_by(
                    versao_id=projeto_assessment.versao_assessment_id,
                    ativo=True
                ).all()
                
                for dominio in dominios:
                    # Estatísticas do domínio
                    respostas_dominio = Resposta.query.join(Pergunta).filter(
                        Pergunta.dominio_versao_id == dominio.id,
                        Resposta.projeto_id == projeto.id
                    ).all()
                    
                    if respostas_dominio:
                        pontuacoes = [r.nota for r in respostas_dominio if r.nota is not None]
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
                            if resposta.nota is not None and resposta.nota <= 2:
                                dominio_data['perguntas_criticas'].append({
                                    'pergunta': resposta.pergunta.texto,
                                    'pontuacao': resposta.nota,
                                    'comentario': resposta.comentario or ''
                                })
                        
                        projeto_data['dominios'].append(dominio_data)
        
            elif projeto_assessment.tipo_assessment_id:
                # Sistema antigo  
                dominios = Dominio.query.filter_by(
                    tipo_assessment_id=projeto_assessment.tipo_assessment_id,
                    ativo=True
                ).all()
                
                for dominio in dominios:
                    # Estatísticas do domínio
                    respostas_dominio = Resposta.query.join(Pergunta).filter(
                        Pergunta.dominio_id == dominio.id,
                        Resposta.projeto_id == projeto.id
                    ).all()
                    
                    if respostas_dominio:
                        pontuacoes = [r.nota for r in respostas_dominio if r.nota is not None]
                        comentarios = [r.comentario for r in respostas_dominio if r.comentario and r.comentario.strip()]
                        
                        dominio_data = {
                            'nome': dominio.nome,
                            'descricao': dominio.descricao,
                            'total_perguntas': len(respostas_dominio),
                            'pontuacao_media': sum(pontuacoes) / len(pontuacoes) if pontuacoes else 0,
                            'pontuacao_maxima': max(pontuacoes) if pontuacoes else 0,
                            'pontuacao_minima': min(pontuacoes) if pontuacoes else 0,
                            'total_comentarios': len(comentarios),
                            'comentarios_destaque': comentarios[:5],
                            'perguntas_criticas': []
                        }
                        
                        # Perguntas com pontuação baixa (críticas)
                        for resposta in respostas_dominio:
                            if resposta.nota is not None and resposta.nota <= 2:
                                dominio_data['perguntas_criticas'].append({
                                    'pergunta': resposta.pergunta.texto,
                                    'pontuacao': resposta.nota,
                                    'comentario': resposta.comentario or ''
                                })
                        
                        projeto_data['dominios'].append(dominio_data)
    
    except Exception as e:
        logging.error(f"Erro ao coletar dados do domínio: {e}")
        # Continuar sem dados de domínio se houver erro
    
    # Estatísticas gerais
    try:
        total_respostas = Resposta.query.filter_by(projeto_id=projeto.id).count()
        respostas_com_pontuacao = Resposta.query.filter(
            Resposta.projeto_id == projeto.id,
            Resposta.nota.isnot(None)
        ).all()
        
        if respostas_com_pontuacao:
            pontuacoes_gerais = [r.nota for r in respostas_com_pontuacao]
            projeto_data['estatisticas_gerais'] = {
                'total_respostas': total_respostas,
                'pontuacao_media_geral': sum(pontuacoes_gerais) / len(pontuacoes_gerais),
                'total_dominios': len(projeto_data['dominios']),
                'total_respondentes': len(projeto_data['respondentes'])
            }
    except Exception as e:
        logging.error(f"Erro ao calcular estatísticas gerais: {e}")
        projeto_data['estatisticas_gerais'] = {}
    
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