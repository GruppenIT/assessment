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
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus import Image
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
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from io import BytesIO

class RelatorioPDF:
    """Classe para geração de relatórios PDF completos e formais"""
    
    def __init__(self, projeto):
        # Recarregar o projeto do banco para garantir dados atualizados
        from models.projeto import Projeto
        self.projeto = Projeto.query.get(projeto.id)
        self.story = []
        self.styles = getSampleStyleSheet()
        self.page_number = 0
        self.total_pages = 0
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
            fontName='Helvetica',
            wordWrap='LTR'
        ))
        
        # Estilo para descrição das perguntas
        self.styles.add(ParagraphStyle(
            name='DescricaoPergunta',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            leftIndent=0,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            wordWrap='LTR'
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
        
        # Estilo para referências em itálico e azul
        self.styles.add(ParagraphStyle(
            name='Referencia',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=colors.darkblue,
            leftIndent=0,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
            wordWrap='LTR'
        ))
        
        # Estilo para comentários em itálico e verde
        self.styles.add(ParagraphStyle(
            name='Comentario',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=colors.darkgreen,
            leftIndent=10,
            spaceAfter=4
        ))
        
        # Estilo para recomendações em negrito e laranja
        self.styles.add(ParagraphStyle(
            name='Recomendacao',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=colors.darkblue,
            leftIndent=0,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
            wordWrap='LTR'
        ))
        
        # Estilo para assinatura
        self.styles.add(ParagraphStyle(
            name='Assinatura',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=8,
            fontName='Helvetica'
        ))
    
    def gerar_relatorio_completo(self):
        """Gera o relatório PDF completo"""
        # Inicializar contador de perguntas
        self._numero_pergunta = 0
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
        
        # Gerar PDF com callback para cabeçalho/rodapé
        doc.build(self.story, onFirstPage=self._primeira_pagina, onLaterPages=self._demais_paginas)
        return temp_filename
    
    def _primeira_pagina(self, canvas, doc):
        """Callback para primeira página (capa) - sem cabeçalho/rodapé"""
        pass
    
    def _demais_paginas(self, canvas, doc):
        """Callback para demais páginas - com cabeçalho e rodapé"""
        canvas.saveState()
        
        # CABEÇALHO
        # Logo do sistema à esquerda
        try:
            # Importar modelo Logo aqui para evitar dependências circulares
            from models.logo import Logo
            
            # Buscar logo ativo do sistema
            logo_sistema = Logo.query.filter_by(ativo=True).first()
            
            logo_encontrado = False
            if logo_sistema and logo_sistema.caminho_arquivo:
                logo_path = logo_sistema.caminho_arquivo
                # O caminho no banco é 'logos/filename.png', mas o real é 'static/uploads/logos/filename.png'
                if logo_path.startswith('logos/'):
                    logo_path = os.path.join('static', 'uploads', logo_path)
                elif not logo_path.startswith('static/'):
                    logo_path = os.path.join('static', 'uploads', logo_path.lstrip('/'))
                
                if os.path.exists(logo_path):
                    canvas.drawImage(logo_path, 1*inch, A4[1] - 0.9*inch, width=0.8*inch, height=0.4*inch, preserveAspectRatio=True)
                    logo_encontrado = True
            
            # Se não encontrou logo do sistema, usar fallback
            if not logo_encontrado:
                canvas.setFont('Helvetica-Bold', 8)
                canvas.setFillColor(HexColor('#2c3e50'))
                canvas.drawString(1*inch, A4[1] - 0.7*inch, 'GRUPPEN IT SECURITY')
                
        except Exception as e:
            # Fallback: texto simples
            canvas.setFont('Helvetica-Bold', 8)
            canvas.setFillColor(HexColor('#2c3e50'))
            canvas.drawString(1*inch, A4[1] - 0.7*inch, 'GRUPPEN IT SECURITY')
        
        # Nome cliente e projeto no centro
        canvas.setFont('Helvetica', 9)
        cliente_nome = self.projeto.cliente.nome or 'Cliente'
        projeto_nome = self.projeto.nome or 'Projeto'
        texto_centro = f"{cliente_nome} - {projeto_nome} - 2025"
        text_width = canvas.stringWidth(texto_centro, 'Helvetica', 9)
        canvas.drawString((A4[0] - text_width) / 2, A4[1] - 0.7*inch, texto_centro)
        
        # Número da página à direita
        page_num = canvas.getPageNumber()
        canvas.drawRightString(A4[0] - 1*inch, A4[1] - 0.7*inch, f"Página {page_num:02d}")
        
        # RODAPÉ
        canvas.setFont('Helvetica-Oblique', 8)
        rodape_texto = "DOCUMENTO CONFIDENCIAL - Este relatório contém informações privilegiadas destinadas exclusivamente ao cliente."
        text_width_rodape = canvas.stringWidth(rodape_texto, 'Helvetica-Oblique', 8)
        canvas.drawString((A4[0] - text_width_rodape) / 2, 0.5*inch, rodape_texto)
        
        canvas.restoreState()
    
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
        Cliente: {self.projeto.cliente.nome}<br/>
        Projeto: {self.projeto.nome}<br/>
        Data de Geração: {format_datetime_local(datetime.utcnow(), '%d/%m/%Y %H:%M')}
        """
        self.story.append(Paragraph(dados_cliente, self.styles['Normal']))
        
        # Logo do cliente (se disponível)  
        if hasattr(self.projeto.cliente, 'logo_path') and self.projeto.cliente.logo_path:
            try:
                logo_path = os.path.join('static', 'uploads', self.projeto.cliente.logo_path)
                if os.path.exists(logo_path):
                    self.story.append(Spacer(1, 20))
                    logo_cliente = Image(logo_path, width=2*inch, height=1*inch, kind='proportional')
                    logo_cliente.hAlign = 'CENTER'
                    self.story.append(logo_cliente)
            except Exception:
                pass
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
            ['Razão Social:', cliente.razao_social or 'Não informado'],
            ['Nome Fantasia:', cliente.nome or 'Não informado'],
            ['CNPJ:', cliente.cnpj or 'Não informado'],
            ['Localidade:', cliente.localidade or 'Não informado'],
            ['Segmento:', cliente.segmento or 'Não informado']
        ]
        
        tabela_cliente = Table(dados_cliente, colWidths=[4*inch, 3*inch])
        tabela_cliente.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('WORDWRAP', (1, 0), (1, -1), 1),
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
            headers = ['Nome', 'Email', 'Login', 'Respostas']
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
                ('WORDWRAP', (0, 1), (-1, -1), 1),
            ]))
            
            self.story.append(tabela_respondentes)
        else:
            self.story.append(Paragraph("Nenhum respondente cadastrado.", self.styles['TextoJustificado']))
        
        self.story.append(Spacer(1, 20))
    
    def _adicionar_dados_projeto(self):
        """Adiciona seção com dados do projeto"""
        self.story.append(Paragraph("3. DADOS DO PROJETO", self.styles['TituloCapitulo']))
        
        dados_projeto = [
            ['Nome:', self.projeto.nome],
            ['Descrição:', self.projeto.descricao or 'Não informado'],
            ['Data de Abertura:', format_date_local(self.projeto.data_criacao) if self.projeto.data_criacao else 'Não informado'],
            ['Data de Conclusão:', format_date_local(self.projeto.data_finalizacao) if self.projeto.data_finalizacao else 'Em andamento'],
            ['Progresso Geral:', f"{self.projeto.get_progresso_geral()}%"]
        ]
        
        tabela_projeto = Table(dados_projeto, colWidths=[3*inch, 4*inch])
        tabela_projeto.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('WORDWRAP', (1, 0), (1, -1), 1),
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
                self.story.append(Paragraph(tipo.nome, self.styles['Subtitulo']))
                
                # Informações básicas sem descrição
                dados_basicos = [
                    ['Domínios:', str(dominios_count)],
                    ['Perguntas:', str(perguntas_count)],
                    ['Status:', 'Finalizado' if projeto_assessment.finalizado else 'Em andamento']
                ]
                
                tabela_basica = Table(dados_basicos, colWidths=[2*inch, 5*inch])
                tabela_basica.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                self.story.append(tabela_basica)
                
                # Descrição em parágrafo separado para quebra correta
                if tipo.descricao:
                    self.story.append(Spacer(1, 6))
                    self.story.append(Paragraph(f"Descrição: {tipo.descricao}", self.styles['TextoJustificado']))
                self.story.append(Spacer(1, 15))
        
        self.story.append(Spacer(1, 20))
    
    def _adicionar_introducao(self):
        """Adiciona seção de introdução"""
        self.story.append(Paragraph("5. INTRODUÇÃO", self.styles['TituloCapitulo']))
        
        # Usar introdução gerada por IA se disponível
        if hasattr(self.projeto, 'introducao_ia') and self.projeto.introducao_ia:
            try:
                # Se for JSON, extrair o texto
                if self.projeto.introducao_ia.strip().startswith('{'):
                    introducao_data = json.loads(self.projeto.introducao_ia)
                    texto_introducao = introducao_data.get('introducao', '')
                else:
                    # Se for texto simples
                    texto_introducao = self.projeto.introducao_ia
                
                if texto_introducao:
                    # Remover tags HTML e processar em parágrafos
                    import re
                    texto_limpo = re.sub(r'<[^>]+>', '', texto_introducao)
                    paragrafos = texto_limpo.split('\n\n')
                    for paragrafo in paragrafos:
                        if paragrafo.strip():
                            self.story.append(Paragraph(paragrafo.strip(), self.styles['TextoJustificado']))
                else:
                    self._adicionar_introducao_padrao()
            except (json.JSONDecodeError, KeyError, TypeError):
                self._adicionar_introducao_padrao()
        else:
            self._adicionar_introducao_padrao()
    
    def _adicionar_introducao_padrao(self):
        """Adiciona introdução padrão quando IA não está disponível"""
        texto_padrao = "Este relatório apresenta os resultados de um assessment de maturidade em segurança da informação, desenvolvido para avaliar o nível atual de implementação de controles e práticas de segurança na organização."
        self.story.append(Paragraph(texto_padrao, self.styles['TextoJustificado']))
        
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
            
            self.story.append(Paragraph(tipo.nome, self.styles['Subtitulo']))
            
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
                        respostas_dominio.append(resposta.nota)
                        todas_respostas.append(resposta.nota)
                
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
                    f"Score Geral: {score_geral:.1f}/5.0",
                    self.styles['TextoJustificado']
                ))
                self.story.append(Spacer(1, 10))
            
            # Tabela de scores por domínio
            if dados_dominios:
                headers = ['Domínio', 'Score', 'Respostas']
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
                
                # Gerar e adicionar gráfico radar
                try:
                    grafico_path = self._gerar_grafico_radar(tipo, dados_dominios)
                    if grafico_path and os.path.exists(grafico_path):
                        self.story.append(Paragraph("Análise Visual por Domínio", self.styles['Subtitulo']))
                        self.story.append(Spacer(1, 10))
                        
                        # Adicionar imagem do gráfico radar
                        img = Image(grafico_path, width=4.5*inch, height=4.5*inch)
                        img.hAlign = 'CENTER'
                        self.story.append(img)
                        self.story.append(Spacer(1, 20))
                        
                        # Limpar arquivo temporário
                        try:
                            os.unlink(grafico_path)
                        except:
                            pass
                except Exception as e:
                    # Se houver erro na geração do gráfico, continuar sem ele
                    print(f"Erro ao gerar gráfico radar: {e}")
                    pass
        
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
            
            self.story.append(Paragraph(tipo.nome, self.styles['Subtitulo']))
            
            for dominio in dominios_query.order_by('ordem'):
                self.story.append(Paragraph(dominio.nome, ParagraphStyle(
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
                        # Pergunta numerada sem "Pergunta:"
                        numero_pergunta = getattr(self, '_numero_pergunta', 0) + 1
                        setattr(self, '_numero_pergunta', numero_pergunta)
                        
                        self.story.append(Paragraph(f"{numero_pergunta}. {pergunta.texto}", 
                                                  ParagraphStyle(name='PerguntaMemorial',
                                                                parent=self.styles['Normal'],
                                                                fontSize=10,
                                                                fontName='Helvetica-Bold',
                                                                spaceAfter=6,
                                                                alignment=TA_JUSTIFY,
                                                                wordWrap='LTR')))
                        
                        # Descrição em itálico e menor, sem "Descrição:"
                        if pergunta.descricao:
                            self.story.append(Paragraph(pergunta.descricao, self.styles['DescricaoPergunta']))
                        
                        # Referência sem recuo, cor azul
                        if pergunta.referencia:
                            self.story.append(Paragraph(f"Referência: {pergunta.referencia}", self.styles['Referencia']))
                        
                        # Pontuação
                        self.story.append(Paragraph(f"Pontuação: {resposta.nota}/5", 
                                                  ParagraphStyle(name='PontuacaoMemorial',
                                                                parent=self.styles['Normal'],
                                                                fontSize=10,
                                                                fontName='Helvetica-Bold',
                                                                textColor=colors.darkred,
                                                                spaceAfter=4)))
                        
                        # Comentário com formatação especial
                        if resposta.comentario:
                            self.story.append(Paragraph(f"Comentário: {resposta.comentario}", self.styles['Comentario']))
                        
                        # Dados técnicos
                        self.story.append(Paragraph(f"Respondente: {resposta.respondente.nome if resposta.respondente else 'Não identificado'} | Data: {format_datetime_local(resposta.data_resposta) if resposta.data_resposta else 'Não informado'}", 
                                                  ParagraphStyle(name='DadosTecnicosMemorial',
                                                                parent=self.styles['Normal'],
                                                                fontSize=8,
                                                                textColor=colors.grey,
                                                                spaceAfter=4)))
                        
                        # Recomendação por último, mesma formatação que referência
                        if pergunta.recomendacao:
                            self.story.append(Paragraph(f"Recomendação: {pergunta.recomendacao}", self.styles['Recomendacao']))
                        
                        self.story.append(Spacer(1, 10))
        
        self.story.append(PageBreak())
    
    def _adicionar_consideracoes_finais(self):
        """Adiciona considerações finais"""
        self.story.append(Paragraph("8. CONSIDERAÇÕES FINAIS", self.styles['TituloCapitulo']))
        
        # Debug removido - funcionalidade corrigida
        
        if self.projeto.consideracoes_finais_ia:
            try:
                # Sempre usar como texto simples (evitando problemas de JSON)
                texto_consideracoes = self.projeto.consideracoes_finais_ia.strip()
                
                if texto_consideracoes:
                    # Remover tags HTML se houver
                    import re
                    texto_limpo = re.sub(r'<[^>]+>', '', texto_consideracoes)
                    paragrafos = texto_limpo.split('\n\n')
                    for paragrafo in paragrafos:
                        if paragrafo.strip():
                            self.story.append(Paragraph(paragrafo.strip(), self.styles['TextoJustificado']))
                else:
                    self.story.append(Paragraph("Considerações finais não disponíveis.", self.styles['TextoJustificado']))
            except Exception as e:
                print(f"DEBUG PDF: Erro ao processar considerações finais: {e}")
                self.story.append(Paragraph("Erro ao processar considerações finais.", self.styles['TextoJustificado']))
        else:
            self.story.append(Paragraph("Considerações finais não geradas.", self.styles['TextoJustificado']))
        
        self.story.append(Spacer(1, 30))
    
    def _adicionar_assinatura(self):
        """Adiciona seção de assinatura sem título separado"""
        # Data e local à direita
        data_atual = datetime.now().strftime("%d de %B de %Y")
        meses = {
            'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
            'April': 'abril', 'May': 'maio', 'June': 'junho',
            'July': 'julho', 'August': 'agosto', 'September': 'setembro', 
            'October': 'outubro', 'November': 'novembro', 'December': 'dezembro'
        }
        for en, pt in meses.items():
            data_atual = data_atual.replace(en, pt)
        
        self.story.append(Paragraph(f"Porto Alegre, {data_atual}", 
                                  ParagraphStyle(name='DataLocal',
                                                parent=self.styles['Normal'],
                                                fontSize=10,
                                                alignment=TA_RIGHT,
                                                spaceAfter=40,
                                                fontName='Helvetica')))
        
        # Linha para assinatura à esquerda
        self.story.append(Paragraph("_" * 60, 
                                  ParagraphStyle(name='LinhaAssinatura',
                                                parent=self.styles['Normal'],
                                                fontSize=10,
                                                alignment=TA_LEFT,
                                                spaceAfter=10,
                                                fontName='Helvetica')))
        
        # Nome e dados do avaliador à esquerda
        nome_avaliador = self.projeto.nome_avaliador or "Nome do Avaliador"
        email_avaliador = self.projeto.email_avaliador or "email@avaliador.com"
        
        self.story.append(Paragraph(nome_avaliador, 
                                  ParagraphStyle(name='NomeAvaliador',
                                                parent=self.styles['Normal'],
                                                fontSize=11,
                                                alignment=TA_LEFT,
                                                fontName='Helvetica-Bold',
                                                spaceAfter=4)))
        
        self.story.append(Paragraph("Consultor em Segurança da Informação", 
                                  ParagraphStyle(name='CargoAvaliador',
                                                parent=self.styles['Normal'],
                                                fontSize=10,
                                                alignment=TA_LEFT,
                                                fontName='Helvetica',
                                                spaceAfter=4)))
        
        self.story.append(Paragraph(f"Email: {email_avaliador}", 
                                  ParagraphStyle(name='EmailAvaliador',
                                                parent=self.styles['Normal'],
                                                fontSize=10,
                                                alignment=TA_LEFT,
                                                fontName='Helvetica')))

    def _gerar_grafico_radar(self, tipo_assessment, dados_dominios):
        """Gera gráfico radar para os domínios de um assessment"""
        if not dados_dominios:
            return None
        
        try:
            # Configurar matplotlib para usar backend não-interativo
            plt.switch_backend('Agg')
            
            # Extrair dados
            labels = [dado[0] for dado in dados_dominios]
            values = [float(dado[1]) for dado in dados_dominios]
            
            # Configurar o gráfico radar
            N = len(labels)
            if N == 0:
                return None
                
            # Calcular ângulos para cada eixo
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Fechar o círculo
            
            # Adicionar o primeiro valor no final para fechar o gráfico
            values += values[:1]
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
            
            # Plotar a área
            ax.plot(angles, values, 'o-', linewidth=2, label=tipo_assessment.nome, color='#6f42c1')
            ax.fill(angles, values, alpha=0.25, color='#6f42c1')
            
            # Configurar labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, fontsize=10)
            
            # Configurar escala radial
            ax.set_ylim(0, 5)
            ax.set_yticks([0, 1, 2, 3, 4, 5])
            ax.set_yticklabels(['0', '1', '2', '3', '4', '5'], fontsize=8)
            ax.grid(True)
            
            # Adicionar título
            plt.title(f'Assessment: {tipo_assessment.nome}', size=14, fontweight='bold', pad=20)
            
            # Configurar layout
            plt.tight_layout()
            
            # Salvar em arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                plt.savefig(tmp_file.name, format='png', dpi=150, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                plt.close()
                return tmp_file.name
                
        except Exception as e:
            print(f"Erro na geração do gráfico radar: {e}")
            plt.close('all')
            return None


def gerar_relatorio_pdf_completo(projeto):
    """Função principal para gerar relatório PDF completo"""
    relatorio = RelatorioPDF(projeto)
    return relatorio.gerar_relatorio_completo()