"""
Utilitário para envio de e-mails via SMTP
Suporte para autenticação básica e OAuth2 (Microsoft 365)
"""

import smtplib
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import msal
import requests
from models.parametro_sistema import ParametroSistema

logger = logging.getLogger(__name__)

class EmailSender:
    """Classe para envio de e-mails com diferentes métodos de autenticação"""
    
    def __init__(self):
        """Inicializa configurações SMTP do sistema"""
        self.config = ParametroSistema.get_smtp_config()
    
    def _get_oauth2_token(self):
        """Obtém access token via OAuth2 (Microsoft 365)"""
        try:
            tenant_id = self.config['smtp_tenant_id']
            client_id = self.config['smtp_client_id']
            client_secret = self.config['smtp_client_secret']
            refresh_token = self.config['smtp_refresh_token']
            
            # Criar aplicação MSAL
            authority = f"https://login.microsoftonline.com/{tenant_id}"
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=authority
            )
            
            # Usar refresh token para obter novo access token
            result = app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=["https://outlook.office365.com/.default"]
            )
            
            if "access_token" in result:
                return result["access_token"]
            else:
                error_msg = result.get("error_description", "Erro desconhecido ao obter token")
                logger.error(f"Erro OAuth2: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter token OAuth2: {str(e)}")
            return None
    
    def _enviar_smtp_basico(self, destinatarios, assunto, corpo_html, corpo_texto=None, anexos=None):
        """Envia e-mail usando autenticação básica SMTP"""
        try:
            # Configurações
            servidor = self.config['smtp_server']
            porta = int(self.config['smtp_port'])
            use_tls = self.config['smtp_use_tls']
            usuario = self.config['smtp_username']
            senha = self.config['smtp_password']
            remetente_email = self.config['smtp_from_email']
            remetente_nome = self.config['smtp_from_name']
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{remetente_nome} <{remetente_email}>"
            msg['To'] = ', '.join(destinatarios) if isinstance(destinatarios, list) else destinatarios
            msg['Subject'] = assunto
            
            # Adicionar corpo em texto plano (fallback)
            if corpo_texto:
                part_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
                msg.attach(part_texto)
            
            # Adicionar corpo HTML
            part_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Adicionar anexos se houver
            if anexos:
                for anexo in anexos:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(anexo['conteudo'])
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={anexo["nome"]}')
                    msg.attach(part)
            
            # Conectar e enviar
            if use_tls:
                server = smtplib.SMTP(servidor, porta)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(servidor, porta)
            
            server.login(usuario, senha)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"E-mail enviado com sucesso via SMTP básico para {msg['To']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via SMTP básico: {str(e)}")
            return False
    
    def _enviar_oauth2(self, destinatarios, assunto, corpo_html, corpo_texto=None, anexos=None):
        """Envia e-mail usando OAuth2 (Microsoft 365)"""
        try:
            # Obter access token
            access_token = self._get_oauth2_token()
            if not access_token:
                logger.error("Não foi possível obter access token OAuth2")
                return False
            
            # Configurações
            servidor = self.config['smtp_server']
            porta = int(self.config['smtp_port'])
            remetente_email = self.config['smtp_from_email']
            remetente_nome = self.config['smtp_from_name']
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{remetente_nome} <{remetente_email}>"
            msg['To'] = ', '.join(destinatarios) if isinstance(destinatarios, list) else destinatarios
            msg['Subject'] = assunto
            
            # Adicionar corpo em texto plano (fallback)
            if corpo_texto:
                part_texto = MIMEText(corpo_texto, 'plain', 'utf-8')
                msg.attach(part_texto)
            
            # Adicionar corpo HTML
            part_html = MIMEText(corpo_html, 'html', 'utf-8')
            msg.attach(part_html)
            
            # Adicionar anexos se houver
            if anexos:
                for anexo in anexos:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(anexo['conteudo'])
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={anexo["nome"]}')
                    msg.attach(part)
            
            # Conectar com OAuth2
            server = smtplib.SMTP(servidor, porta)
            server.starttls()
            
            # Autenticar com OAuth2 (deve ser base64, não hex!)
            auth_string = f"user={remetente_email}\1auth=Bearer {access_token}\1\1"
            auth_base64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
            server.docmd('AUTH', 'XOAUTH2 ' + auth_base64)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"E-mail enviado com sucesso via OAuth2 para {msg['To']}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via OAuth2: {str(e)}")
            return False
    
    def enviar_email(self, destinatarios, assunto, corpo_html, corpo_texto=None, anexos=None):
        """
        Envia e-mail usando a configuração apropriada (OAuth2 ou básica)
        
        Args:
            destinatarios: Lista de e-mails ou string com e-mail único
            assunto: Assunto do e-mail
            corpo_html: Corpo do e-mail em HTML
            corpo_texto: Corpo do e-mail em texto plano (opcional, usado como fallback)
            anexos: Lista de dicionários com 'nome' e 'conteudo' (opcional)
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        # Validar configurações
        if not self.config['smtp_server'] or not self.config['smtp_from_email']:
            logger.error("Configurações SMTP incompletas. Configure em /admin/parametros/smtp")
            return False
        
        # Converter destinatários para lista se necessário
        if isinstance(destinatarios, str):
            destinatarios = [destinatarios]
        
        # Escolher método de autenticação
        auth_type = self.config['smtp_auth_type']
        
        if auth_type == 'oauth2':
            return self._enviar_oauth2(destinatarios, assunto, corpo_html, corpo_texto, anexos)
        else:
            return self._enviar_smtp_basico(destinatarios, assunto, corpo_html, corpo_texto, anexos)


def enviar_alerta_novo_lead(lead, tipo_assessment):
    """
    Envia alerta de novo lead para os destinatários configurados no tipo de assessment
    
    Args:
        lead: Objeto Lead com informações do contato
        tipo_assessment: Objeto AssessmentTipo com configurações
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Verificar se há destinatários configurados
        if not tipo_assessment.email_destinatarios:
            logger.info(f"Nenhum destinatário configurado para o tipo {tipo_assessment.nome}")
            return False
        
        # Separar e-mails (por vírgula ou ponto-e-vírgula)
        destinatarios = []
        for email in tipo_assessment.email_destinatarios.replace(';', ',').split(','):
            email = email.strip()
            if email:
                destinatarios.append(email)
        
        if not destinatarios:
            logger.warning(f"Nenhum e-mail válido configurado para o tipo {tipo_assessment.nome}")
            return False
        
        # Buscar assessment público e agrupar respostas por domínio
        assessment_publico = lead.assessment_publico
        respostas_por_dominio = []
        
        if assessment_publico:
            # Agrupar respostas por domínio
            dominios = {}
            for resposta in assessment_publico.respostas:
                dominio = resposta.pergunta.dominio_versao
                if dominio.id not in dominios:
                    dominios[dominio.id] = {
                        'nome': dominio.nome,
                        'respostas': []
                    }
                dominios[dominio.id]['respostas'].append({
                    'pergunta': resposta.pergunta.texto,
                    'resposta': resposta.get_texto_resposta(),
                    'valor': resposta.valor
                })
            
            # Converter para lista ordenada
            respostas_por_dominio = list(dominios.values())
        
        # Montar corpo do e-mail
        from flask import render_template, current_app
        
        # Criar contexto de requisição para renderizar template
        with current_app.test_request_context():
            corpo_html = render_template('emails/novo_lead.html', 
                                         lead=lead, 
                                         tipo_assessment=tipo_assessment,
                                         respostas_por_dominio=respostas_por_dominio)
        
        corpo_texto = f"""
Novo Lead Capturado - {tipo_assessment.nome}

Nome: {lead.nome}
E-mail: {lead.email}
Telefone: {lead.telefone or 'Não informado'}
Empresa: {lead.empresa or 'Não informada'}

Pontuação Obtida: {lead.pontuacao_geral:.1f}%

Este lead respondeu ao assessment público e está aguardando contato.

Acesse o sistema para visualizar os detalhes completos e o histórico de interações.
        """
        
        # Enviar e-mail
        sender = EmailSender()
        assunto = f"Novo Lead Capturado - {tipo_assessment.nome}"
        
        resultado = sender.enviar_email(
            destinatarios=destinatarios,
            assunto=assunto,
            corpo_html=corpo_html,
            corpo_texto=corpo_texto
        )
        
        if resultado:
            logger.info(f"Alerta de novo lead enviado para {', '.join(destinatarios)}")
        else:
            logger.error(f"Falha ao enviar alerta de novo lead")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao enviar alerta de novo lead: {str(e)}")
        return False


def validar_configuracao_smtp():
    """
    Valida se as configurações SMTP estão completas
    
    Returns:
        dict: {'valido': bool, 'mensagem': str}
    """
    config = ParametroSistema.get_smtp_config()
    
    if not config['smtp_server']:
        return {'valido': False, 'mensagem': 'Servidor SMTP não configurado'}
    
    if not config['smtp_from_email']:
        return {'valido': False, 'mensagem': 'E-mail remetente não configurado'}
    
    if config['smtp_auth_type'] == 'oauth2':
        if not config['smtp_client_id'] or not config['smtp_client_secret'] or not config['smtp_refresh_token']:
            return {'valido': False, 'mensagem': 'Credenciais OAuth2 incompletas'}
    else:
        if not config['smtp_username'] or not config['smtp_password']:
            return {'valido': False, 'mensagem': 'Usuário/senha SMTP não configurados'}
    
    return {'valido': True, 'mensagem': 'Configurações SMTP completas'}


def enviar_resultado_assessment(assessment_publico, email_destino, tipo_assessment):
    """
    Envia resultado formatado do assessment por email
    
    Args:
        assessment_publico: Objeto AssessmentPublico com respostas
        email_destino: Email do destinatário
        tipo_assessment: Objeto TipoAssessment
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    try:
        # Calcular pontuação geral
        pontuacao_geral = assessment_publico.calcular_pontuacao_geral()
        
        # Obter domínios respondidos com pontuações
        dominios_dados = []
        for dominio in assessment_publico.get_dominios_respondidos():
            pontuacao_dominio = assessment_publico.calcular_pontuacao_dominio(dominio.id)
            
            dominios_dados.append({
                'dominio': dominio,
                'pontuacao': pontuacao_dominio,
                'recomendacao': None
            })
        
        # Gerar recomendações com OpenAI
        from utils.publico_utils import gerar_recomendacoes_ia
        
        try:
            logger.info(f"Gerando recomendações IA para email do assessment público {assessment_publico.id}")
            recomendacoes = gerar_recomendacoes_ia(assessment_publico, dominios_dados)
            
            for i, dominio_data in enumerate(dominios_dados):
                if i < len(recomendacoes):
                    dominio_data['recomendacao'] = recomendacoes[i]
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações IA para email: {e}")
            # Usar recomendações padrão
            for dominio_data in dominios_dados:
                pontuacao = dominio_data['pontuacao']
                dominio_nome = dominio_data['dominio'].nome
                dominio_data['recomendacao'] = (
                    f"Com base na pontuação de {pontuacao:.0f}%, recomenda-se revisar e fortalecer "
                    f"as práticas relacionadas a {dominio_nome}."
                )
        
        # Montar corpo do e-mail
        from flask import render_template, current_app
        
        with current_app.test_request_context():
            corpo_html = render_template('emails/resultado_assessment.html',
                                         assessment_publico=assessment_publico,
                                         tipo_assessment=tipo_assessment,
                                         pontuacao_geral=pontuacao_geral,
                                         dominios_dados=dominios_dados)
        
        corpo_texto = f"""
Resultado do Assessment - {tipo_assessment.nome}

Pontuação Geral: {pontuacao_geral:.1f}%

Obrigado por responder ao nosso assessment. Acesse o link abaixo para visualizar seu resultado completo.
        """
        
        # Enviar e-mail
        sender = EmailSender()
        assunto = f"Resultado do seu Assessment - {tipo_assessment.nome}"
        
        resultado = sender.enviar_email(
            destinatarios=[email_destino],  # Converter string para lista
            assunto=assunto,
            corpo_html=corpo_html,
            corpo_texto=corpo_texto
        )
        
        if resultado:
            logger.info(f"Resultado do assessment enviado para {email_destino}")
        else:
            logger.error(f"Falha ao enviar resultado do assessment para {email_destino}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao enviar resultado do assessment: {str(e)}")
        return False
