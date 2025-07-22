"""
Utilitários para integração com OpenAI
"""

import json
import logging
import time
from datetime import datetime
from openai import OpenAI
from app import db
from models.parametro_sistema import ParametroSistema
from utils.timezone_utils import format_date_local, format_datetime_local
from utils.openai_monitor import payload_monitor, monitor_openai_request

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
            
            logging.debug(f"OpenAI config: api_key_configured={config.get('api_key_configured')}, assistant_name={self.assistant_name}")
            
            if api_key and api_key.strip():
                # Validar formato da chave
                if not api_key.startswith('sk-'):
                    logging.error(f"OpenAI API key tem formato inválido. Deve começar com 'sk-'")
                    return
                
                if len(api_key) < 40:
                    logging.error(f"OpenAI API key muito curta. Tamanho: {len(api_key)}")
                    return
                
                self.client = OpenAI(
                    api_key=api_key,
                    timeout=60,  # 60 segundos timeout
                    max_retries=3  # 3 tentativas
                )
                logging.info(f"Cliente OpenAI inicializado com assistant: {self.assistant_name}")
                logging.debug(f"API key válida: {api_key[:10]}...{api_key[-6:]}")
            else:
                logging.warning("API Key OpenAI não configurada ou vazia")
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
            # Analisar payload antes do envio
            analysis = payload_monitor.analyze_project_payload(projeto_data)
            
            # Log warnings críticos
            for warning in analysis.get('warnings', []):
                if 'CRÍTICO' in warning:
                    logging.error(f"PAYLOAD INTRODUÇÃO: {warning}")
                elif 'ATENÇÃO' in warning:
                    logging.warning(f"PAYLOAD INTRODUÇÃO: {warning}")
            
            start_time = time.time()
            
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
            
            response_time = time.time() - start_time
            
            # Log métricas de sucesso
            payload_monitor.log_request(
                operation='gerar_introducao',
                payload_analysis=analysis,
                response_time=response_time,
                success=True
            )
            
            logging.info(f"Introdução gerada com sucesso: "
                        f"{analysis['payload_size']['estimated_tokens']:,} tokens enviados, "
                        f"{response_time:.2f}s de resposta")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Log erro com análise do payload
            if 'analysis' in locals():
                payload_monitor.log_request(
                    operation='gerar_introducao',
                    payload_analysis=analysis,
                    response_time=time.time() - start_time if 'start_time' in locals() else 0,
                    success=False,
                    error=str(e)
                )
            
            logging.error(f"Erro ao gerar introdução do projeto: {e}")
            return None
    
    def gerar_analise_dominio(self, dominio_data):
        """Gera análise de um domínio específico usando IA"""
        if not self.is_configured():
            logging.error("Assistente OpenAI não configurado para gerar análise")
            return None
        
        import time
        
        max_tentativas = 3
        tentativa = 0
        
        while tentativa < max_tentativas:
            try:
                tentativa += 1
                logging.info(f"Gerando análise para domínio: {dominio_data.get('dominio', {}).get('nome', 'Unknown')} (tentativa {tentativa})")
                
                # Preparar prompt específico para análise de domínio
                prompt = f"""
                Como analista especializado em assessments de maturidade organizacional, analise o domínio abaixo:

                **DADOS DO DOMÍNIO (JSON):**
                {json.dumps(dominio_data, indent=2, ensure_ascii=False)}

                **INSTRUÇÕES CRÍTICAS PARA ANÁLISE:**
                1. Escreva um parágrafo técnico como se você fosse o analista que avaliou pessoalmente as respostas
                2. Mencione o nome do domínio e sua importância no contexto do assessment
                3. **ANÁLISE INTEGRADA DE NOTAS E COMENTÁRIOS:**
                   - Para cada questão, considere TANTO a nota quanto o comentário do respondente
                   - Se um comentário menciona planos futuros, iniciativas em andamento, ou contexto adicional, INCLUA essas informações na análise
                   - Use frases como "embora o cliente tenha mencionado que...", "conforme relatado pelo respondente...", "considerando que a organização planeja..."
                   - Identifique contradições entre notas baixas e comentários que indicam melhorias planejadas
                4. **CONTEXTUALIZAÇÃO BASEADA EM COMENTÁRIOS:**
                   - Se comentários mencionam cronogramas (ex: "planejado para 2025"), incorpore isso nas recomendações
                   - Se comentários explicam limitações atuais mas indicam progressos futuros, reconheça isso
                   - Se comentários fornecem detalhes sobre implementações parciais, considere na avaliação
                5. Identifique os principais pontos fortes baseado nas respostas com notas altas E comentários positivos
                6. Identifique pontos fracos considerando notas baixas MAS também o contexto dos comentários
                7. **RECOMENDAÇÕES CONTEXTUALIZADAS:**
                   - Se um comentário indica que algo já está sendo planejado/implementado, ajuste a recomendação
                   - Exemplo: "embora a política esteja planejada para conclusão em 2025, recomendamos acelerar o processo devido à criticidade..."
                8. Forneça uma avaliação geral que INTEGRE notas numéricas com insights dos comentários

                **FORMATO DE SAÍDA:**
                Retorne apenas o parágrafo de análise, sem explicações adicionais ou formatação markdown.
                Use linguagem técnica, objetiva e profissional, como um consultor especializado que leu e analisou cada comentário individual.
                """
                
                logging.debug(f"Enviando prompt para OpenAI (tamanho: {len(prompt)} caracteres)")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=[
                        {"role": "system", "content": f"Você é o {self.assistant_name}. Analise domínios de assessments de maturidade organizacional com expertise técnica e visão analítica profunda."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                    timeout=15  # Timeout mais curto ainda
                )
                
                analise = response.choices[0].message.content.strip()
                logging.info(f"Análise gerada com sucesso (tamanho: {len(analise)} caracteres)")
                return analise
                
            except Exception as e:
                logging.error(f"Erro na tentativa {tentativa}: {e}")
                
                # Se é erro SSL ou timeout e ainda há tentativas, aguardar e tentar novamente
                if tentativa < max_tentativas and ("SSL" in str(e) or "timeout" in str(e).lower() or "recv" in str(e)):
                    wait_time = tentativa * 2  # Aumentar tempo de espera a cada tentativa
                    logging.info(f"Aguardando {wait_time} segundos antes da próxima tentativa...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Se não é erro de conectividade ou acabaram as tentativas
                    logging.error(f"Falha definitiva ao gerar análise do domínio: {e}")
                    return None
        
        logging.error("Todas as tentativas falharam")
        return None

    def gerar_consideracoes_finais(self, dados_projeto):
        """Gera considerações finais para o projeto baseado em todas as respostas"""
        if not self.is_configured():
            logging.error("Assistente OpenAI não configurado para gerar considerações finais")
            logging.error(f"Cliente OpenAI: {self.client}, API Key configurada: {bool(self.client)}")
            # Forçar reinicialização do cliente
            self._initialize_client()
            if not self.is_configured():
                return None
        
        # Analisar payload antes do processamento
        analysis = payload_monitor.analyze_project_payload(dados_projeto)
        
        # Log crítico para payloads muito grandes
        for warning in analysis.get('warnings', []):
            if 'CRÍTICO' in warning:
                logging.error(f"PAYLOAD CONSIDERAÇÕES FINAIS: {warning}")
            elif 'ATENÇÃO' in warning:
                logging.warning(f"PAYLOAD CONSIDERAÇÕES FINAIS: {warning}")
        
        # Se payload for muito grande, tentar otimizar
        payload_size = analysis['payload_size']['estimated_tokens']
        if payload_size > 80000:  # Se muito grande, reduzir dados
            logging.warning(f"Payload muito grande ({payload_size:,} tokens). Tentando otimizar...")
            dados_projeto = self._otimizar_payload_consideracoes(dados_projeto)
            analysis = payload_monitor.analyze_project_payload(dados_projeto)
            logging.info(f"Payload otimizado para {analysis['payload_size']['estimated_tokens']:,} tokens")
        
        max_tentativas = 3
        tentativa = 0
        
        while tentativa < max_tentativas:
            try:
                tentativa += 1
                start_time = time.time()
                
                logging.info(f"Gerando considerações finais para projeto (tentativa {tentativa})")
                logging.info(f"Payload: {analysis['payload_size']['estimated_tokens']:,} tokens, "
                           f"{analysis['payload_size']['bytes']:,} bytes")
                
                # Preparar prompt específico para considerações finais
                prompt = f"""
                Como consultor especializado da GRUPPEN IT SECURITY em assessments de maturidade organizacional, elabore as CONSIDERAÇÕES FINAIS do relatório baseado nos dados completos do projeto abaixo:

                **DADOS COMPLETOS DO PROJETO (JSON):**
                {json.dumps(dados_projeto, indent=2, ensure_ascii=False)}

                **ESTRUTURA OBRIGATÓRIA PARA AS CONSIDERAÇÕES FINAIS:**

                1. **PARÁGRAFO INTRODUTÓRIO:**
                   - Inicie apresentando as conclusões do projeto
                   - Cite quantos assessments foram realizados e quais tipos (ex: "O projeto compreendeu 1 assessment de Cibersegurança...")
                   - Mencione o escopo e metodologia utilizada

                2. **ANÁLISE POR ASSESSMENT:**
                   - Para cada tipo de assessment presente nos dados:
                     - Um parágrafo introdutório sobre o assessment específico
                     - Subtópicos em parágrafos separados para cada domínio com:
                       * Nome do domínio e sua nota/desempenho
                       * Análise dos pontos fortes identificados
                       * Gaps e oportunidades de melhoria
                       * Recomendações específicas e acionáveis

                3. **ANÁLISE FINAL ABRANGENTE:**
                   - Parágrafo com opinião geral sobre o panorama de maturidade
                   - Priorização das ações por impacto e urgência
                   - Cronograma sugerido de implementação (curto, médio, longo prazo)
                   - Recursos necessários (pessoas, tecnologia, processos)

                4. **PARÁGRAFO DE CONCLUSÃO E ENCERRAMENTO:**
                   - Agradecimento pela oportunidade de trabalhar no projeto
                   - Colocar a Gruppen IT Security à disposição para quaisquer ações advindas do relatório
                   - Encerramento formal e profissional

                **DIRETRIZES TÉCNICAS:**
                - Use dados específicos dos assessments (scores, percentuais, números)
                - **INTEGRE COMENTÁRIOS DOS RESPONDENTES:** Sempre que um comentário fornecer contexto adicional, planos futuros, ou explicações, incorpore essas informações na análise
                - **CONSIDERAÇÕES CONTEXTUAIS:** Se comentários mencionam cronogramas, limitações, ou iniciativas em andamento, reflita isso nas recomendações
                - Use frases como "embora o cliente tenha relatado que...", "conforme mencionado pelo respondente...", "considerando os planos informados..."
                - Seja técnico mas acessível para gestores
                - Mencione frameworks relevantes quando aplicável (ISO 27001, NIST, etc.)
                - Priorize recomendações por criticidade e viabilidade, considerando o contexto dos comentários

                **FORMATO DE SAÍDA:**
                Retorne apenas o texto das considerações finais, sem formatação markdown ou títulos.
                O texto deve ter entre 1000-1800 palavras, bem estruturado em parágrafos.
                IMPORTANTE: Complete todas as frases e termine com um ponto final para indicar conclusão.
                """
                
                logging.debug(f"Enviando prompt para OpenAI (tamanho: {len(prompt)} caracteres)")
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Usar modelo mais rápido para evitar timeout
                    messages=[
                        {"role": "system", "content": f"Você é o {self.assistant_name}. Elabore considerações finais técnicas e estratégicas para relatórios de assessment de maturidade organizacional."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2500,  # Aumentar limite para texto completo (aproximadamente 1500-2000 palavras)
                    temperature=0.7,
                    timeout=45  # Timeout mais longo para respostas longas
                )
                
                consideracoes = response.choices[0].message.content.strip()
                
                # Verificar se o texto está completo (termina com ponto)
                termina_completo = consideracoes.endswith('.') or consideracoes.endswith('!') or consideracoes.endswith('?')
                
                response_time = time.time() - start_time
                
                # Log métricas de sucesso
                payload_monitor.log_request(
                    operation='gerar_consideracoes_finais',
                    payload_analysis=analysis,
                    response_time=response_time,
                    success=True
                )
                
                logging.info(f"Considerações finais geradas com sucesso: "
                           f"{analysis['payload_size']['estimated_tokens']:,} tokens enviados, "
                           f"{response_time:.2f}s de resposta, "
                           f"Completo: {termina_completo}")
                
                return consideracoes
                
            except Exception as e:
                response_time = time.time() - start_time if 'start_time' in locals() else 0
                logging.error(f"Erro na tentativa {tentativa}: {e}")
                
                # Log erro se for a última tentativa
                if tentativa >= max_tentativas:
                    payload_monitor.log_request(
                        operation='gerar_consideracoes_finais',
                        payload_analysis=analysis,
                        response_time=response_time,
                        success=False,
                        error=str(e)
                    )
                
                # Verificar se é erro de conectividade para retry
                error_str = str(e).lower()
                connectivity_errors = ["ssl", "timeout", "recv", "connection", "network", "read timed out", "connection reset"]
                
                is_connectivity_error = any(keyword in error_str for keyword in connectivity_errors)
                
                if tentativa < max_tentativas and is_connectivity_error:
                    wait_time = tentativa * 3  # Aumentar tempo de espera
                    logging.info(f"Erro de conectividade detectado: {type(e).__name__}. Aguardando {wait_time} segundos antes da próxima tentativa...")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"Falha definitiva ao gerar considerações finais: {e}")
                    return None
        
        logging.error("Todas as tentativas falharam")
        return None
    
    def _otimizar_payload_consideracoes(self, dados_projeto):
        """Otimiza payload para considerações finais removendo dados desnecessários"""
        try:
            # Criar cópia dos dados
            dados_otimizados = dados_projeto.copy()
            
            # Reduzir detalhes de perguntas muito longas
            if 'dominios' in dados_otimizados:
                for dominio in dados_otimizados['dominios']:
                    if 'perguntas' in dominio:
                        for pergunta in dominio['perguntas']:
                            # Manter apenas campos essenciais para análise
                            campos_essenciais = ['id', 'texto', 'respostas']
                            pergunta_otimizada = {k: v for k, v in pergunta.items() if k in campos_essenciais}
                            
                            # Limitar texto da pergunta se muito longo
                            if 'texto' in pergunta_otimizada and len(pergunta_otimizada['texto']) > 300:
                                pergunta_otimizada['texto'] = pergunta_otimizada['texto'][:300] + '...'
                            
                            # Limitar comentários das respostas
                            if 'respostas' in pergunta_otimizada:
                                for resposta in pergunta_otimizada['respostas']:
                                    if 'comentario' in resposta and resposta['comentario'] and len(resposta['comentario']) > 200:
                                        resposta['comentario'] = resposta['comentario'][:200] + '...'
                            
                            pergunta.clear()
                            pergunta.update(pergunta_otimizada)
            
            logging.info("Payload otimizado para considerações finais")
            return dados_otimizados
            
        except Exception as e:
            logging.error(f"Erro ao otimizar payload: {e}")
            return dados_projeto  # Retornar original se falhar

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
                "nome": projeto.cliente.nome if projeto.cliente else "Cliente não especificado",
                "razao_social": projeto.cliente.razao_social if projeto.cliente else None,
                "localidade": projeto.cliente.localidade if projeto.cliente else None,
                "segmento": projeto.cliente.segmento if projeto.cliente else None
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
                "descricao": tipo.descricao if hasattr(tipo, 'descricao') else None
            })
        
        # Adicionar estatísticas básicas
        dados["estatisticas"] = {
            "total_respondentes": len(dados["respondentes"]),
            "total_tipos_assessment": len(dados["tipos_assessment"]),
            "progresso_geral": projeto.get_progresso_geral()
        }
        
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

def coletar_dados_dominio_para_ia(projeto, dominio):
    """Coleta dados de um domínio específico para análise IA"""
    try:
        from models.resposta import Resposta
        from models.pergunta import Pergunta
        
        dados_dominio = {
            "dominio": {
                "nome": dominio.nome,
                "descricao": dominio.descricao if hasattr(dominio, 'descricao') else None,
                "ordem": dominio.ordem if hasattr(dominio, 'ordem') else None
            },
            "perguntas_respostas": [],
            "estatisticas": {
                "total_perguntas": 0,
                "total_respostas": 0,
                "nota_media": 0
            }
        }
        
        # Identificar se é sistema novo ou antigo
        perguntas_dominio = []
        if hasattr(dominio, 'versao_id'):
            # Sistema novo - domínio versionado
            perguntas_dominio = Pergunta.query.filter_by(
                dominio_versao_id=dominio.id,
                ativo=True
            ).order_by(Pergunta.ordem).all()
        else:
            # Sistema antigo - domínio tradicional
            perguntas_dominio = Pergunta.query.filter_by(
                dominio_id=dominio.id,
                ativo=True
            ).order_by(Pergunta.ordem).all()
        
        notas_coletadas = []
        
        for pergunta in perguntas_dominio:
            # Buscar respostas desta pergunta no projeto
            respostas_pergunta = Resposta.query.filter_by(
                projeto_id=projeto.id,
                pergunta_id=pergunta.id
            ).order_by(Resposta.data_resposta.desc()).all()
            
            if respostas_pergunta:
                # Pegar a resposta mais recente (colaborativa)
                resposta_final = respostas_pergunta[0]
                
                dados_dominio["perguntas_respostas"].append({
                    "pergunta": {
                        "texto": pergunta.texto,
                        "ordem": pergunta.ordem,
                        "referencia": pergunta.referencia if hasattr(pergunta, 'referencia') else None,
                        "recomendacao": pergunta.recomendacao if hasattr(pergunta, 'recomendacao') else None
                    },
                    "resposta": {
                        "nota": resposta_final.nota,
                        "comentario": resposta_final.comentario,
                        "respondente": resposta_final.respondente.nome if resposta_final.respondente else "Sistema",
                        "data_resposta": resposta_final.data_resposta.strftime('%d/%m/%Y às %H:%M') if resposta_final.data_resposta else None
                    },
                    "historico_respostas": len(respostas_pergunta)
                })
                
                notas_coletadas.append(resposta_final.nota)
        
        # Calcular estatísticas
        dados_dominio["estatisticas"]["total_perguntas"] = len(perguntas_dominio)
        dados_dominio["estatisticas"]["total_respostas"] = len(dados_dominio["perguntas_respostas"])
        dados_dominio["estatisticas"]["nota_media"] = round(sum(notas_coletadas) / len(notas_coletadas) if notas_coletadas else 0, 2)
        
        return dados_dominio
        
    except Exception as e:
        logging.error(f"Erro ao coletar dados do domínio para IA: {e}")
        return None

def gerar_analise_dominios_ia(projeto):
    """Função principal para gerar análise dos domínios com IA"""
    try:
        logging.info(f"Iniciando geração de análise dos domínios para projeto {projeto.id}")
        
        # Verificar se projeto está finalizado
        if not projeto.is_totalmente_finalizado():
            logging.warning(f"Projeto {projeto.id} não está totalmente finalizado")
            return {
                'erro': 'O projeto deve estar totalmente finalizado para gerar a análise dos domínios.'
            }
        
        # Inicializar assistente
        logging.info("Inicializando assistente OpenAI")
        assistant = OpenAIAssistant()
        if not assistant.is_configured():
            logging.error("Assistente OpenAI não está configurado")
            return {
                'erro': 'Integração com ChatGPT não configurada. Configure a API Key e o nome do Assistant em Parâmetros do Sistema.'
            }
        
        # Coletar todos os domínios do projeto
        dominios_analises = {}
        total_dominios = 0
        dominios_processados = 0
        
        for projeto_assessment in projeto.assessments:
            if not projeto_assessment.finalizado:
                continue
                
            # Identificar domínios do assessment
            dominios_query = None
            if projeto_assessment.versao_assessment_id:
                # Sistema novo
                from models.assessment_version import AssessmentDominio
                dominios_query = AssessmentDominio.query.filter_by(
                    versao_id=projeto_assessment.versao_assessment.id,
                    ativo=True
                ).order_by(AssessmentDominio.ordem)
            elif projeto_assessment.tipo_assessment_id:
                # Sistema antigo
                from models.dominio import Dominio
                dominios_query = Dominio.query.filter_by(
                    tipo_assessment_id=projeto_assessment.tipo_assessment_id,
                    ativo=True
                ).order_by(Dominio.ordem)
            
            if not dominios_query:
                continue
                
            tipo_nome = (projeto_assessment.versao_assessment.tipo.nome 
                        if projeto_assessment.versao_assessment_id 
                        else projeto_assessment.tipo_assessment.nome)
            
            if tipo_nome not in dominios_analises:
                dominios_analises[tipo_nome] = {}
            
            for dominio in dominios_query:
                total_dominios += 1
                
                # Coletar dados do domínio
                logging.info(f"Coletando dados para domínio: {dominio.nome}")
                dados_dominio = coletar_dados_dominio_para_ia(projeto, dominio)
                if not dados_dominio:
                    logging.warning(f"Não foi possível coletar dados para domínio: {dominio.nome}")
                    continue
                
                # Gerar análise do domínio
                logging.info(f"Gerando análise IA para domínio: {dominio.nome}")
                try:
                    analise = assistant.gerar_analise_dominio(dados_dominio)
                    if analise:
                        dominios_analises[tipo_nome][dominio.nome] = {
                            'analise': analise,
                            'estatisticas': dados_dominio['estatisticas'],
                            'gerado_em': datetime.now().isoformat()
                        }
                        dominios_processados += 1
                        logging.info(f"Análise gerada com sucesso para domínio: {dominio.nome}")
                    else:
                        logging.warning(f"Análise vazia para domínio: {dominio.nome}")
                except Exception as e:
                    logging.error(f"Erro ao gerar análise para domínio {dominio.nome}: {e}")
                    # Em caso de erro SSL/timeout, continuar com os próximos domínios
                    continue
        
        if not dominios_analises:
            return {
                'erro': 'Nenhum domínio encontrado para análise.'
            }
        
        resultado_final = {
            'analises': dominios_analises,
            'assistant_name': assistant.assistant_name,
            'total_dominios': total_dominios,
            'dominios_processados': dominios_processados,
            'gerado_em': datetime.now().isoformat()
        }
        
        # Se processou pelo menos alguns domínios com sucesso, considerar sucesso parcial
        if dominios_processados > 0:
            logging.info(f"Processamento concluído: {dominios_processados}/{total_dominios} domínios")
            return resultado_final
        else:
            return {
                'erro': f'Não foi possível processar nenhum domínio. Total tentativas: {total_dominios}'
            }
        
    except Exception as e:
        logging.error(f"Erro ao gerar análise dos domínios IA: {e}")
        return {
            'erro': f'Erro interno: {str(e)}'
        }

def coletar_dados_projeto_completo_para_ia(projeto):
    """Coleta dados completos do projeto para geração de considerações finais"""
    try:
        logging.info(f"Coletando dados completos do projeto {projeto.id}")
        
        dados_projeto = {
            'projeto': {
                'id': projeto.id,
                'nome': projeto.nome,
                'cliente': projeto.cliente.nome,
                'data_criacao': projeto.data_criacao.isoformat() if projeto.data_criacao else None,
                'data_conclusao': projeto.data_conclusao.isoformat() if projeto.data_conclusao else None,
                'data_finalizacao': projeto.data_finalizacao.isoformat() if projeto.data_finalizacao else None
            },
            'assessments': []
        }
        
        for projeto_assessment in projeto.assessments:
            if not projeto_assessment.finalizado:
                continue
                
            # Calcular score médio das respostas deste assessment
            from models.resposta import Resposta
            from models.pergunta import Pergunta
            
            score_medio = 0
            if projeto_assessment.versao_assessment_id:
                from models.assessment_version import AssessmentDominio
                respostas_query = db.session.query(Resposta.nota).join(
                    Pergunta, Resposta.pergunta_id == Pergunta.id
                ).join(
                    AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
                ).filter(
                    Resposta.projeto_id == projeto.id,
                    AssessmentDominio.versao_id == projeto_assessment.versao_assessment_id,
                    Resposta.nota.isnot(None)
                )
            elif projeto_assessment.tipo_assessment_id:
                from models.dominio import Dominio
                respostas_query = db.session.query(Resposta.nota).join(
                    Pergunta, Resposta.pergunta_id == Pergunta.id
                ).join(
                    Dominio, Pergunta.dominio_id == Dominio.id
                ).filter(
                    Resposta.projeto_id == projeto.id,
                    Dominio.tipo_assessment_id == projeto_assessment.tipo_assessment_id,
                    Resposta.nota.isnot(None)
                )
            else:
                respostas_query = None
            
            if respostas_query:
                notas = [nota for (nota,) in respostas_query.all()]
                score_medio = round(sum(notas) / len(notas), 2) if notas else 0
            
            # Dados do assessment
            assessment_data = {
                'tipo': (projeto_assessment.versao_assessment.tipo.nome 
                        if projeto_assessment.versao_assessment_id 
                        else projeto_assessment.tipo_assessment.nome),
                'score_medio': score_medio,
                'progresso_percentual': projeto_assessment.get_progresso_percentual(),
                'finalizado': projeto_assessment.finalizado,
                'data_finalizacao': projeto_assessment.data_finalizacao.isoformat() if projeto_assessment.data_finalizacao else None,
                'dominios': []
            }
            
            # Identificar domínios do assessment
            dominios_query = None
            if projeto_assessment.versao_assessment_id:
                from models.assessment_version import AssessmentDominio
                dominios_query = AssessmentDominio.query.filter_by(
                    versao_id=projeto_assessment.versao_assessment.id,
                    ativo=True
                ).order_by(AssessmentDominio.ordem)
            elif projeto_assessment.tipo_assessment_id:
                from models.dominio import Dominio
                dominios_query = Dominio.query.filter_by(
                    tipo_assessment_id=projeto_assessment.tipo_assessment_id,
                    ativo=True
                ).order_by(Dominio.ordem)
            
            if not dominios_query:
                continue
            
            # Coletar dados de cada domínio
            for dominio in dominios_query:
                dominio_data = coletar_dados_dominio_para_ia(projeto, dominio)
                if dominio_data:
                    assessment_data['dominios'].append(dominio_data)
            
            dados_projeto['assessments'].append(assessment_data)
        
        # Estatísticas gerais do projeto
        from models.resposta import Resposta
        total_respostas = Resposta.query.join(Resposta.pergunta).filter(
            Resposta.projeto_id == projeto.id,
            Resposta.nota.isnot(None)
        ).count()
        
        dados_projeto['estatisticas_gerais'] = {
            'total_respostas': total_respostas,
            'total_assessments': len(dados_projeto['assessments']),
            'respondentes': len(set(r.respondente_id for r in projeto.respostas if r.respondente_id))
        }
        
        logging.info(f"Dados completos coletados: {len(dados_projeto['assessments'])} assessments, {total_respostas} respostas")
        return dados_projeto
        
    except Exception as e:
        logging.error(f"Erro ao coletar dados completos do projeto: {e}")
        return None

def gerar_consideracoes_finais_projeto(projeto):
    """Gera considerações finais completas para o projeto"""
    try:
        logging.info(f"Iniciando geração de considerações finais para projeto {projeto.id}")
        
        # Verificar se projeto está finalizado
        if not projeto.is_totalmente_finalizado():
            return {
                'erro': 'O projeto deve estar totalmente finalizado para gerar as considerações finais.'
            }
        
        # Inicializar assistente
        assistant = OpenAIAssistant()
        if not assistant.is_configured():
            return {
                'erro': 'Integração com ChatGPT não configurada.'
            }
        
        # Coletar dados completos do projeto
        dados_projeto = coletar_dados_projeto_completo_para_ia(projeto)
        if not dados_projeto:
            return {
                'erro': 'Não foi possível coletar dados do projeto para análise.'
            }
        
        # Gerar considerações finais
        consideracoes = assistant.gerar_consideracoes_finais(dados_projeto)
        if not consideracoes:
            return {
                'erro': 'Não foi possível gerar as considerações finais.'
            }
        
        return {
            'consideracoes': consideracoes,
            'assistant_name': assistant.assistant_name,
            'gerado_em': datetime.now().isoformat(),
            'dados_utilizados': {
                'total_assessments': len(dados_projeto['assessments']),
                'total_respostas': dados_projeto['estatisticas_gerais']['total_respostas']
            }
        }
        
    except Exception as e:
        logging.error(f"Erro crítico na geração de considerações finais: {e}")
        return {
            'erro': f'Erro durante processamento: {str(e)}'
        }