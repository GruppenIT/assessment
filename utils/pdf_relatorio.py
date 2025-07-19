"""
Utilitário para geração de relatórios PDF completos e formais
"""

import os
import json
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics import renderPDF
from models.assessment_version import AssessmentDominio
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from models.respondente import Respondente
from app import db
from utils.timezone_utils import format_datetime_local, format_date_local
from sqlalchemy import func

class RelatorioPDF:
    """Classe para geração de relatórios PDF completos e formais"""
    
    def __init__(self, projeto):
        self.projeto = projeto
        self.story = []
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configurar estilos personalizados para o relatório"""
        # Estilo para títulos principais
        self.styles.add(ParagraphStyle(
            name='TituloCapitulo',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=30,
            textColor=HexColor('#2c3e50'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=15,
            textColor=HexColor('#34495e'),
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto normal justificado
        self.styles.add(ParagraphStyle(
            name='TextoJustificado',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Estilo para dados técnicos
        self.styles.add(ParagraphStyle(
            name='DadosTecnicos',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            leftIndent=15,
            fontName='Helvetica'
        ))
        
        # Estilo para assinatura
        self.styles.add(ParagraphStyle(
            name='Assinatura',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=8,
            fontName='Helvetica'
        ))
    
    def gerar_relatorio_completo(self):
        """Gera o relatório PDF completo"""
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Criar documento
        doc = SimpleDocTemplate(
            temp_filename,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=20*mm,
            title=f"Relatório de Assessment - {self.projeto.nome}"
        )
        
        # Construir conteúdo
        self._adicionar_capa()
        self._adicionar_indice()
        self._adicionar_dados_cliente()
        self._adicionar_dados_respondentes()
        self._adicionar_dados_projeto()
        self._adicionar_dados_assessments()
        self._adicionar_introducao()
        self._adicionar_scores()
        self._adicionar_memorial_respostas()
        self._adicionar_consideracoes_finais()
        self._adicionar_assinatura()
        
        # Gerar PDF
        doc.build(self.story)
        return temp_filename
    
    def _adicionar_capa(self):
        """Adiciona a capa do relatório"""
        # Logo/Título da empresa
        titulo_empresa = Paragraph("GRUPPEN IT SECURITY", self.styles['Title'])
        self.story.append(titulo_empresa)
        self.story.append(Spacer(1, 30))
        
        # Título do relatório
        titulo_relatorio = Paragraph(
            "RELATÓRIO DE ASSESSMENT DE MATURIDADE<br/>EM SEGURANÇA DA INFORMAÇÃO",
            ParagraphStyle(
                name='TituloRelatorio',
                parent=self.styles['Title'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=HexColor('#2c3e50')
            )
        )
        self.story.append(titulo_relatorio)
        self.story.append(Spacer(1, 50))
        
        # Dados do cliente
        dados_cliente = f"""
        <b>Cliente:</b> {self.projeto.cliente.nome}<br/>
        <b>Projeto:</b> {self.projeto.nome}<br/>
        <b>Data de Geração:</b> {format_datetime_local(datetime.utcnow(), '%d/%m/%Y %H:%M')}
        """
        self.story.append(Paragraph(dados_cliente, self.styles['Normal']))
        self.story.append(Spacer(1, 100))
        
        # Rodapé da capa
        rodape_capa = Paragraph(
            "Este relatório contém informações confidenciais sobre a maturidade<br/>" +
            "em segurança da informação da organização avaliada.",
            ParagraphStyle(
                name='RodapeCapa',
                parent=self.styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=HexColor('#7f8c8d')
            )
        )
        self.story.append(rodape_capa)
        self.story.append(PageBreak())
    
    def _adicionar_indice(self):
        """Adiciona o índice do relatório"""
        self.story.append(Paragraph("ÍNDICE", self.styles['TituloCapitulo']))
        
        indice_items = [
            "1. DADOS DO CLIENTE",
            "2. DADOS DOS RESPONDENTES", 
            "3. DADOS DO PROJETO",
            "4. DADOS DOS ASSESSMENTS",
            "5. INTRODUÇÃO",
            "6. SCORES E RESULTADOS",
            "7. MEMORIAL DE RESPOSTAS",
            "8. CONSIDERAÇÕES FINAIS",
            "9. ASSINATURA"
        ]
        
        for item in indice_items:
            self.story.append(Paragraph(item, self.styles['DadosTecnicos']))
        
        self.story.append(PageBreak())
    
    def _adicionar_dados_cliente(self):
        """Adiciona seção com dados do cliente"""
        self.story.append(Paragraph("1. DADOS DO CLIENTE", self.styles['TituloCapitulo']))
        
        cliente = self.projeto.cliente
        dados_cliente = [
            ['<b>Razão Social:</b>', cliente.razao_social or 'Não informado'],
            ['<b>Nome Fantasia:</b>', cliente.nome or 'Não informado'],
            ['<b>CNPJ:</b>', cliente.cnpj or 'Não informado'],
            ['<b>Localidade:</b>', cliente.localidade or 'Não informado'],
            ['<b>Segmento:</b>', cliente.segmento or 'Não informado'],
            ['<b>Data de Cadastro:</b>', format_date_local(cliente.data_cadastro) if cliente.data_cadastro else 'Não informado']
        ]
        
        tabela_cliente = Table(dados_cliente, colWidths=[4*inch, 3*inch])
        tabela_cliente.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.story.append(tabela_cliente)
        self.story.append(Spacer(1, 20))
    
    def _adicionar_dados_respondentes(self):
        """Adiciona seção com dados dos respondentes"""
        self.story.append(Paragraph("2. DADOS DOS RESPONDENTES", self.styles['TituloCapitulo']))
        
        respondentes = []
        for projeto_resp in self.projeto.respondentes:
            respondente = projeto_resp.respondente
            total_respostas = Resposta.query.filter_by(
                projeto_id=self.projeto.id,
                respondente_id=respondente.id
            ).count()
            
            respondentes.append([
                respondente.nome,
                respondente.email,
                respondente.login,
                str(total_respostas)
            ])
        
        if respondentes:
            headers = ['<b>Nome</b>', '<b>Email</b>', '<b>Login</b>', '<b>Respostas</b>']
            dados_respondentes = [headers] + respondentes
            
            tabela_respondentes = Table(dados_respondentes, colWidths=[2*inch, 2.5*inch, 1.5*inch, 1*inch])
            tabela_respondentes.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            self.story.append(tabela_respondentes)
        else:
            self.story.append(Paragraph("Nenhum respondente cadastrado.", self.styles['TextoJustificado']))
        
        self.story.append(Spacer(1, 20))
    
    def _adicionar_dados_projeto(self):
        """Adiciona seção com dados do projeto"""
        self.story.append(Paragraph("3. DADOS DO PROJETO", self.styles['TituloCapitulo']))
        
        dados_projeto = [
            ['<b>Nome:</b>', self.projeto.nome],
            ['<b>Descrição:</b>', self.projeto.descricao or 'Não informado'],
            ['<b>Data de Abertura:</b>', format_date_local(self.projeto.data_criacao) if self.projeto.data_criacao else 'Não informado'],
            ['<b>Data de Conclusão:</b>', format_date_local(self.projeto.data_finalizacao) if self.projeto.data_finalizacao else 'Em andamento'],
            ['<b>Progresso Geral:</b>', f"{self.projeto.get_progresso_geral()}%"]
        ]
        
        tabela_projeto = Table(dados_projeto, colWidths=[3*inch, 4*inch])
        tabela_projeto.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        self.story.append(tabela_projeto)
        self.story.append(Spacer(1, 20))
    
    def _adicionar_dados_assessments(self):
        """Adiciona seção com dados dos assessments"""
        self.story.append(Paragraph("4. DADOS DOS ASSESSMENTS", self.styles['TituloCapitulo']))
        
        for projeto_assessment in self.projeto.assessments:
            # Determinar tipo e versão
            tipo = None
            versao = None
            dominios_count = 0
            perguntas_count = 0
            
            if projeto_assessment.versao_assessment_id:
                versao = projeto_assessment.versao_assessment
                tipo = versao.tipo
                dominios_count = AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True).count()
                
                # Contar perguntas
                for dominio in AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True):
                    perguntas_count += Pergunta.query.filter_by(dominio_versao_id=dominio.id, ativo=True).count()
            
            elif projeto_assessment.tipo_assessment_id:
                tipo = projeto_assessment.tipo_assessment
                dominios_count = Dominio.query.filter_by(tipo_assessment_id=tipo.id, ativo=True).count()
                perguntas_count = db.session.query(func.count(Pergunta.id)).join(
                    Dominio, Pergunta.dominio_id == Dominio.id
                ).filter(Dominio.tipo_assessment_id == tipo.id, Pergunta.ativo == True).scalar()
            
            if tipo:
                self.story.append(Paragraph(f"<b>{tipo.nome}</b>", self.styles['Subtitulo']))
                
                dados_assessment = [
                    ['<b>Descrição:</b>', tipo.descricao or 'Não informado'],
                    ['<b>Domínios:</b>', str(dominios_count)],
                    ['<b>Perguntas:</b>', str(perguntas_count)],
                    ['<b>Status:</b>', 'Finalizado' if projeto_assessment.finalizado else 'Em andamento']
                ]
                
                tabela_assessment = Table(dados_assessment, colWidths=[2*inch, 5*inch])
                tabela_assessment.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                self.story.append(tabela_assessment)
                self.story.append(Spacer(1, 15))
        
        self.story.append(Spacer(1, 20))
    
    def _adicionar_introducao(self):
        """Adiciona seção de introdução"""
        self.story.append(Paragraph("5. INTRODUÇÃO", self.styles['TituloCapitulo']))
        
        if self.projeto.introducao_ia:
            try:
                introducao_data = json.loads(self.projeto.introducao_ia)
                texto_introducao = introducao_data.get('introducao', '')
                if texto_introducao:
                    paragrafos = texto_introducao.split('\n\n')
                    for paragrafo in paragrafos:
                        if paragrafo.strip():
                            self.story.append(Paragraph(paragrafo.strip(), self.styles['TextoJustificado']))
                else:
                    self.story.append(Paragraph("Introdução não disponível.", self.styles['TextoJustificado']))
            except (json.JSONDecodeError, KeyError):
                self.story.append(Paragraph("Introdução não disponível.", self.styles['TextoJustificado']))
        else:
            self.story.append(Paragraph("Introdução não gerada.", self.styles['TextoJustificado']))
        
        self.story.append(Spacer(1, 20))
    
    def _adicionar_scores(self):
        """Adiciona seção de scores e resultados"""
        self.story.append(Paragraph("6. SCORES E RESULTADOS", self.styles['TituloCapitulo']))
        
        # Calcular e exibir scores por assessment
        for projeto_assessment in self.projeto.assessments:
            if not projeto_assessment.finalizado:
                continue
            
            # Determinar tipo e versão
            tipo = None
            versao = None
            
            if projeto_assessment.versao_assessment_id:
                versao = projeto_assessment.versao_assessment
                tipo = versao.tipo
                dominios_query = AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True)
            elif projeto_assessment.tipo_assessment_id:
                tipo = projeto_assessment.tipo_assessment
                dominios_query = Dominio.query.filter_by(tipo_assessment_id=tipo.id, ativo=True)
            
            if not tipo:
                continue
            
            self.story.append(Paragraph(f"<b>{tipo.nome}</b>", self.styles['Subtitulo']))
            
            # Calcular score geral
            todas_respostas = []
            dados_dominios = []
            
            for dominio in dominios_query.order_by('ordem'):
                # Buscar perguntas do domínio
                if versao:
                    perguntas_dominio = Pergunta.query.filter_by(
                        dominio_versao_id=dominio.id,
                        ativo=True
                    ).order_by(Pergunta.ordem).all()
                else:
                    perguntas_dominio = Pergunta.query.filter_by(
                        dominio_id=dominio.id,
                        ativo=True
                    ).order_by(Pergunta.ordem).all()
                
                respostas_dominio = []
                for pergunta in perguntas_dominio:
                    resposta = Resposta.query.filter_by(
                        projeto_id=self.projeto.id,
                        pergunta_id=pergunta.id
                    ).order_by(Resposta.data_resposta.desc()).first()
                    
                    if resposta:
                        respostas_dominio.append(resposta.valor)
                        todas_respostas.append(resposta.valor)
                
                # Calcular média do domínio
                if respostas_dominio:
                    media_dominio = sum(respostas_dominio) / len(respostas_dominio)
                    dados_dominios.append([
                        dominio.nome,
                        f"{media_dominio:.1f}",
                        f"{len(respostas_dominio)}/{len(perguntas_dominio)}"
                    ])
            
            # Score geral
            if todas_respostas:
                score_geral = sum(todas_respostas) / len(todas_respostas)
                self.story.append(Paragraph(
                    f"<b>Score Geral: {score_geral:.1f}/5.0</b>",
                    self.styles['TextoJustificado']
                ))
                self.story.append(Spacer(1, 10))
            
            # Tabela de scores por domínio
            if dados_dominios:
                headers = ['<b>Domínio</b>', '<b>Score</b>', '<b>Respostas</b>']
                dados_tabela = [headers] + dados_dominios
                
                tabela_scores = Table(dados_tabela, colWidths=[4*inch, 1.5*inch, 1.5*inch])
                tabela_scores.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                self.story.append(tabela_scores)
                self.story.append(Spacer(1, 20))
        
        self.story.append(PageBreak())
    
    def _adicionar_memorial_respostas(self):
        """Adiciona memorial completo de respostas"""
        self.story.append(Paragraph("7. MEMORIAL DE RESPOSTAS", self.styles['TituloCapitulo']))
        
        for projeto_assessment in self.projeto.assessments:
            if not projeto_assessment.finalizado:
                continue
            
            # Determinar tipo e versão
            tipo = None
            versao = None
            
            if projeto_assessment.versao_assessment_id:
                versao = projeto_assessment.versao_assessment
                tipo = versao.tipo
                dominios_query = AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True)
            elif projeto_assessment.tipo_assessment_id:
                tipo = projeto_assessment.tipo_assessment
                dominios_query = Dominio.query.filter_by(tipo_assessment_id=tipo.id, ativo=True)
            
            if not tipo:
                continue
            
            self.story.append(Paragraph(f"<b>{tipo.nome}</b>", self.styles['Subtitulo']))
            
            for dominio in dominios_query.order_by('ordem'):
                self.story.append(Paragraph(f"<b>{dominio.nome}</b>", ParagraphStyle(
                    name='DominioMemorial',
                    parent=self.styles['Normal'],
                    fontSize=12,
                    spaceAfter=10,
                    spaceBefore=15,
                    textColor=HexColor('#2980b9'),
                    fontName='Helvetica-Bold'
                )))
                
                # Buscar perguntas do domínio
                if versao:
                    perguntas_dominio = Pergunta.query.filter_by(
                        dominio_versao_id=dominio.id,
                        ativo=True
                    ).order_by(Pergunta.ordem).all()
                else:
                    perguntas_dominio = Pergunta.query.filter_by(
                        dominio_id=dominio.id,
                        ativo=True
                    ).order_by(Pergunta.ordem).all()
                
                for pergunta in perguntas_dominio:
                    resposta = Resposta.query.filter_by(
                        projeto_id=self.projeto.id,
                        pergunta_id=pergunta.id
                    ).order_by(Resposta.data_resposta.desc()).first()
                    
                    if resposta:
                        # Montar dados da resposta
                        dados_resposta = [
                            ['<b>Pergunta:</b>', pergunta.texto],
                            ['<b>Descrição:</b>', pergunta.descricao or 'Não informado'],
                            ['<b>Referência:</b>', pergunta.referencia or 'Não informado'],
                            ['<b>Pontuação:</b>', f"{resposta.valor}/5"],
                            ['<b>Comentário:</b>', resposta.comentario or 'Sem comentários'],
                            ['<b>Respondente:</b>', resposta.respondente.nome if resposta.respondente else 'Não identificado'],
                            ['<b>Data:</b>', format_datetime_local(resposta.data_resposta) if resposta.data_resposta else 'Não informado'],
                            ['<b>Recomendação:</b>', pergunta.recomendacao or 'Não informado']
                        ]
                        
                        tabela_resposta = Table(dados_resposta, colWidths=[2*inch, 5*inch])
                        tabela_resposta.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fa')),
                            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
                        ]))
                        
                        self.story.append(tabela_resposta)
                        self.story.append(Spacer(1, 10))
        
        self.story.append(PageBreak())
    
    def _adicionar_consideracoes_finais(self):
        """Adiciona considerações finais"""
        self.story.append(Paragraph("8. CONSIDERAÇÕES FINAIS", self.styles['TituloCapitulo']))
        
        if self.projeto.consideracoes_finais_ia:
            try:
                consideracoes_data = json.loads(self.projeto.consideracoes_finais_ia)
                texto_consideracoes = consideracoes_data.get('consideracoes', '')
                if texto_consideracoes:
                    paragrafos = texto_consideracoes.split('\n\n')
                    for paragrafo in paragrafos:
                        if paragrafo.strip():
                            self.story.append(Paragraph(paragrafo.strip(), self.styles['TextoJustificado']))
                else:
                    self.story.append(Paragraph("Considerações finais não disponíveis.", self.styles['TextoJustificado']))
            except (json.JSONDecodeError, KeyError):
                self.story.append(Paragraph("Considerações finais não disponíveis.", self.styles['TextoJustificado']))
        else:
            self.story.append(Paragraph("Considerações finais não geradas.", self.styles['TextoJustificado']))
        
        self.story.append(Spacer(1, 30))
    
    def _adicionar_assinatura(self):
        """Adiciona seção de assinatura"""
        self.story.append(Paragraph("9. ASSINATURA", self.styles['TituloCapitulo']))
        
        # Data e local
        data_atual = format_datetime_local(datetime.utcnow(), '%d/%m/%Y')
        local_data = f"São Paulo, {data_atual}"
        self.story.append(Paragraph(local_data, self.styles['Assinatura']))
        self.story.append(Spacer(1, 30))
        
        # Linha para assinatura
        linha_assinatura = Drawing(400, 20)
        linha_assinatura.add(Line(50, 10, 350, 10))
        self.story.append(linha_assinatura)
        self.story.append(Spacer(1, 10))
        
        # Dados do avaliador
        if self.projeto.nome_avaliador:
            nome_avaliador = self.projeto.nome_avaliador
            email_avaliador = self.projeto.email_avaliador or ""
            
            assinatura_texto = f"<b>{nome_avaliador}</b><br/>"
            if email_avaliador:
                assinatura_texto += f"{email_avaliador}<br/>"
            assinatura_texto += "Consultor Especialista<br/>Gruppen IT Security"
            
            self.story.append(Paragraph(assinatura_texto, self.styles['Assinatura']))
        else:
            self.story.append(Paragraph(
                "<b>[Nome do Avaliador]</b><br/>Consultor Especialista<br/>Gruppen IT Security",
                self.styles['Assinatura']
            ))


def gerar_relatorio_pdf_completo(projeto):
    """Função principal para gerar relatório PDF completo"""
    relatorio = RelatorioPDF(projeto)
    return relatorio.gerar_relatorio_completo()