"""
Utilitário para geração de PDFs do sistema de assessment
"""

import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from models.assessment_version import AssessmentDominio
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from app import db
from sqlalchemy import func
from flask import current_app

def gerar_relatorio_markdown(projeto):
    """
    Gera um relatório em formato Markdown com a mesma estrutura das estatísticas
    """
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.md', mode='w', encoding='utf-8')
    temp_filename = temp_file.name
    
    # Buscar dados das estatísticas (replicando a lógica da view)
    estatisticas_data = []
    
    for projeto_assessment in projeto.assessments:
        if not projeto_assessment.finalizado:
            continue
            
        # Determinar tipo e versão do assessment
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
        
        # Processar domínios
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
                # Buscar resposta mais recente desta pergunta no projeto
                resposta = Resposta.query.filter_by(
                    projeto_id=projeto.id,
                    pergunta_id=pergunta.id
                ).order_by(Resposta.data_resposta.desc()).first()
                
                if resposta:
                    respostas_dominio.append({
                        'pergunta': pergunta,
                        'resposta_final': resposta
                    })
            
            if respostas_dominio:
                estatisticas_data.append({
                    'dominio': dominio,
                    'tipo': tipo,
                    'respostas': respostas_dominio
                })
    
    # Gerar conteúdo Markdown
    markdown_content = f"""# 📊 RELATÓRIO DE ESTATÍSTICAS

## Informações do Projeto

**📁 Projeto:** {projeto.nome}  
**🏢 Cliente:** {projeto.cliente.nome}  
**📅 Data de Geração:** {datetime.now().strftime('%d/%m/%Y às %H:%M')}  
**🎯 Status:** Finalizado  

---

# 📝 MEMORIAL DE RESPOSTAS E COMENTÁRIOS

"""
    
    for dominio_data in estatisticas_data:
        # Título do domínio
        markdown_content += f"\n## 🔒 {dominio_data['dominio'].nome}\n\n"
        
        for resposta_data in dominio_data['respostas']:
            pergunta = resposta_data['pergunta']
            resposta = resposta_data['resposta_final']
            
            # Determinar nível de maturidade e emoji
            nota = resposta.nota
            if nota == 0:
                nivel = "Inexistente"
                emoji_nivel = "🔴"
            elif nota == 1:
                nivel = "Inicial"
                emoji_nivel = "⚪"
            elif nota == 2:
                nivel = "Básico"
                emoji_nivel = "🟡"
            elif nota == 3:
                nivel = "Intermediário"
                emoji_nivel = "🔵"
            elif nota == 4:
                nivel = "Avançado"
                emoji_nivel = "🟢"
            else:  # nota == 5
                nivel = "Otimizado"
                emoji_nivel = "🟢"
            
            # Container para cada resposta
            markdown_content += f"""
### 📋 Pergunta #{pergunta.ordem}

> **❓ PERGUNTA**  
> **{pergunta.texto}**

"""
            
            if pergunta.descricao:
                markdown_content += f"> *{pergunta.descricao}*\n\n"
            
            # Seção de Resposta
            respondente_nome = resposta.respondente.nome if resposta.respondente else 'Sistema'
            data_resposta = resposta.data_resposta.strftime('%d/%m/%Y às %H:%M')
            
            markdown_content += f"""
> **📊 RESPOSTA**  
> **Pontuação:** {emoji_nivel} **{nota}/5 - {nivel}**  
> **👤 Respondente:** {respondente_nome}  
> **🕒 Data:** {data_resposta}  

"""
            
            if resposta.comentario:
                markdown_content += f"""
> **💬 Comentário do Respondente:**  
> *"{resposta.comentario}"*

"""
            
            # Seção de Feedback Técnico
            if pergunta.referencia or pergunta.recomendacao:
                markdown_content += f"\n> **🎓 FEEDBACK TÉCNICO**\n\n"
                
                if pergunta.referencia:
                    markdown_content += f"""
> **📚 Referência Teórica:**  
> {pergunta.referencia}

"""
                
                if pergunta.recomendacao:
                    markdown_content += f"""
> **💡 Recomendação:**  
> {pergunta.recomendacao}

"""
            
            markdown_content += "\n---\n"
    
    # Adicionar legenda de níveis
    markdown_content += f"""

## 📈 LEGENDA - NÍVEIS DE MATURIDADE

| Faixa | Nível | Emoji | Descrição |
|-------|-------|-------|-----------|
| 0.0 | Inexistente | 🔴 | Nenhum controle implementado |
| 1.0 | Inicial | ⚪ | Práticas informais e não documentadas |
| 2.0 | Básico | 🟡 | Controles definidos, aplicação inconsistente |
| 3.0 | Intermediário | 🔵 | Controles padronizados e repetíveis |
| 4.0 | Avançado | 🟢 | Controles monitorados com métricas |
| 5.0 | Otimizado | 🟢 | Controles integrados e melhorados continuamente |

---

**📄 Relatório gerado automaticamente pelo Sistema de Avaliações de Maturidade**  
**⏰ {datetime.now().strftime('%d/%m/%Y às %H:%M')}**

"""
    
    # Escrever no arquivo
    temp_file.write(markdown_content)
    temp_file.close()
    
    return temp_filename

def gerar_relatorio_estatisticas_visual(projeto):
    """
    Gera um relatório PDF com a mesma identidade visual das estatísticas da web
    """
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_filename = temp_file.name
    temp_file.close()
    
    # Criar documento
    doc = SimpleDocTemplate(
        temp_filename,
        pagesize=A4,
        rightMargin=50, leftMargin=50,
        topMargin=50, bottomMargin=50
    )
    
    # Cores principais (replicando as cores do CSS)
    COR_AZUL = HexColor('#0d6efd')
    COR_VERDE = HexColor('#198754')
    COR_CIANO = HexColor('#0dcaf0')
    COR_AMARELO = HexColor('#ffc107')
    COR_FUNDO_AZUL = HexColor('#f0f7ff')
    COR_FUNDO_VERDE = HexColor('#f0f8f5')
    COR_FUNDO_CIANO = HexColor('#f0fdff')
    
    # Estilos personalizados
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=HexColor('#2c3e50'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    badge_style = ParagraphStyle(
        'BadgeStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=5
    )
    
    pergunta_style = ParagraphStyle(
        'PerguntaStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        leftIndent=15,
        rightIndent=15,
        spaceBefore=5,
        spaceAfter=5
    )
    
    descricao_style = ParagraphStyle(
        'DescricaoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#6c757d'),
        alignment=TA_LEFT,
        leftIndent=15,
        rightIndent=15,
        spaceBefore=2,
        spaceAfter=8
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#6c757d'),
        alignment=TA_LEFT,
        leftIndent=15,
        rightIndent=15,
        spaceBefore=3,
        spaceAfter=3
    )
    
    comentario_style = ParagraphStyle(
        'ComentarioStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=5,
        spaceAfter=5
    )
    
    tecnico_style = ParagraphStyle(
        'TecnicoStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_LEFT,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=3,
        spaceAfter=8
    )
    
    # Função auxiliar para criar caixas coloridas
    def criar_secao_colorida(elementos, cor_badge, cor_fundo, largura=None):
        if largura is None:
            largura = 500
        
        # Tabela para simular fundo colorido
        data = [[elem] for elem in elementos]
        table = Table(data, colWidths=[largura])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), cor_fundo),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 3, cor_badge),
        ]))
        return table
    
    # Elementos do documento
    story = []
    
    # Cabeçalho
    story.append(Paragraph("RELATÓRIO DE ESTATÍSTICAS", title_style))
    story.append(Spacer(1, 15))
    
    # Barra de logos das empresas
    try:
        # Usar caminho absoluto baseado no root_path da aplicação
        base_path = current_app.root_path if current_app else os.path.dirname(os.path.dirname(__file__))
        logos_paths = [
            os.path.join(base_path, 'static', 'img', 'gruppen.png'),
            os.path.join(base_path, 'static', 'img', 'zerobox.png'),
            os.path.join(base_path, 'static', 'img', 'firewall365.png'),
            os.path.join(base_path, 'static', 'img', 'gsecdo.png')
        ]
        
        logos_images = []
        for logo_path in logos_paths:
            if os.path.exists(logo_path):
                img = Image(logo_path, width=80, height=25, kind='proportional')
                logos_images.append(img)
        
        if logos_images:
            # Criar tabela com logos em fundo preto
            logo_table = Table([logos_images], colWidths=[100, 100, 100, 100])
            logo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(logo_table)
            story.append(Spacer(1, 20))
    except Exception as e:
        # Se falhar ao carregar logos, continua sem eles
        pass
    
    story.append(Paragraph(f"<b>Projeto:</b> {projeto.nome}", pergunta_style))
    story.append(Paragraph(f"<b>Cliente:</b> {projeto.cliente.nome}", info_style))
    story.append(Paragraph(f"<b>Data de Geração:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}", info_style))
    story.append(Spacer(1, 30))
    
    # Buscar dados das estatísticas (replicando a lógica da view)
    estatisticas_data = []
    
    for projeto_assessment in projeto.assessments:
        if not projeto_assessment.finalizado:
            continue
            
        # Determinar tipo e versão do assessment
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
        
        # Processar domínios
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
                # Buscar resposta mais recente desta pergunta no projeto
                resposta = Resposta.query.filter_by(
                    projeto_id=projeto.id,
                    pergunta_id=pergunta.id
                ).order_by(Resposta.data_resposta.desc()).first()
                
                if resposta:
                    respostas_dominio.append({
                        'pergunta': pergunta,
                        'resposta_final': resposta
                    })
            
            if respostas_dominio:
                estatisticas_data.append({
                    'dominio': dominio,
                    'tipo': tipo,
                    'respostas': respostas_dominio
                })
    
    # Gerar memorial de respostas com estrutura visual idêntica
    story.append(Paragraph("MEMORIAL DE RESPOSTAS E COMENTÁRIOS", title_style))
    story.append(Spacer(1, 20))
    
    for dominio_data in estatisticas_data:
        # Título do domínio
        story.append(Paragraph(f"<b>{dominio_data['dominio'].nome}</b>", pergunta_style))
        story.append(Spacer(1, 10))
        
        for resposta_data in dominio_data['respostas']:
            pergunta = resposta_data['pergunta']
            resposta = resposta_data['resposta_final']
            
            # Container para cada resposta (simulando o card)
            elementos_resposta = []
            
            # SEÇÃO 1: PERGUNTA (azul)
            elementos_pergunta = []
            elementos_pergunta.append(Paragraph("🔵 PERGUNTA", badge_style))
            elementos_pergunta.append(Paragraph(pergunta.texto, pergunta_style))
            if pergunta.descricao:
                elementos_pergunta.append(Paragraph(pergunta.descricao, descricao_style))
            
            secao_pergunta = criar_secao_colorida(elementos_pergunta, COR_AZUL, COR_FUNDO_AZUL)
            story.append(secao_pergunta)
            story.append(Spacer(1, 2))
            
            # SEÇÃO 2: RESPOSTA (verde)
            elementos_resposta = []
            
            # Determinar nível de maturidade
            nota = resposta.nota
            if nota == 0:
                nivel = "Inexistente"
                cor_badge_nota = colors.red
            elif nota == 1:
                nivel = "Inicial"
                cor_badge_nota = colors.grey
            elif nota == 2:
                nivel = "Básico"
                cor_badge_nota = colors.orange
            elif nota == 3:
                nivel = "Intermediário"
                cor_badge_nota = colors.blue
            elif nota == 4:
                nivel = "Avançado"
                cor_badge_nota = colors.green
            else:  # nota == 5
                nivel = "Otimizado"
                cor_badge_nota = colors.darkgreen
            
            elementos_resposta.append(Paragraph(f"🟢 RESPOSTA - <b>{nota} - {nivel}</b>", badge_style))
            
            respondente_nome = resposta.respondente.nome if resposta.respondente else 'Sistema'
            data_resposta = resposta.data_resposta.strftime('%d/%m/%Y às %H:%M')
            elementos_resposta.append(Paragraph(f"<b>👤 Respondente:</b> {respondente_nome}", info_style))
            elementos_resposta.append(Paragraph(f"<b>🕒 Data:</b> {data_resposta}", info_style))
            
            if resposta.comentario:
                elementos_resposta.append(Spacer(1, 5))
                elementos_resposta.append(Paragraph("<b>💬 Comentário do respondente:</b>", info_style))
                elementos_resposta.append(Paragraph(resposta.comentario, comentario_style))
            
            secao_resposta = criar_secao_colorida(elementos_resposta, COR_VERDE, COR_FUNDO_VERDE)
            story.append(secao_resposta)
            story.append(Spacer(1, 2))
            
            # SEÇÃO 3: FEEDBACK TÉCNICO (ciano) - apenas se houver referência ou recomendação
            if pergunta.referencia or pergunta.recomendacao:
                elementos_feedback = []
                elementos_feedback.append(Paragraph("🔵 FEEDBACK TÉCNICO", badge_style))
                
                if pergunta.referencia:
                    elementos_feedback.append(Paragraph("<b>📚 REFERÊNCIA TEÓRICA:</b>", info_style))
                    elementos_feedback.append(Paragraph(pergunta.referencia, tecnico_style))
                
                if pergunta.recomendacao:
                    if pergunta.referencia:
                        elementos_feedback.append(Spacer(1, 5))
                    elementos_feedback.append(Paragraph("<b>💡 RECOMENDAÇÃO:</b>", info_style))
                    elementos_feedback.append(Paragraph(pergunta.recomendacao, tecnico_style))
                
                secao_feedback = criar_secao_colorida(elementos_feedback, COR_CIANO, COR_FUNDO_CIANO)
                story.append(secao_feedback)
            
            story.append(Spacer(1, 20))
    
    # Construir documento
    doc.build(story)
    
    return temp_filename

def gerar_relatorio_estatisticas(projeto):
    """
    Gera um relatório PDF completo das estatísticas do projeto
    """
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_filename = temp_file.name
    temp_file.close()
    
    # Criar documento
    doc = SimpleDocTemplate(
        temp_filename,
        pagesize=A4,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=18
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=HexColor('#2c3e50'),
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=HexColor('#34495e'),
        alignment=TA_LEFT
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=HexColor('#7f8c8d'),
        alignment=TA_LEFT
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_LEFT
    )
    
    # Elementos do documento
    story = []
    
    # Cabeçalho
    story.append(Paragraph("RELATÓRIO DE ESTATÍSTICAS", title_style))
    story.append(Paragraph(f"Projeto: {projeto.nome}", heading_style))
    story.append(Paragraph(f"Cliente: {projeto.cliente.nome}", normal_style))
    story.append(Paragraph(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", normal_style))
    story.append(Spacer(1, 20))
    
    # Verificar se projeto está finalizado
    finalizados, total_assessments = projeto.get_assessments_finalizados()
    
    if not projeto.is_totalmente_finalizado():
        story.append(Paragraph("ATENÇÃO: Este projeto ainda não está totalmente finalizado.", normal_style))
        story.append(Spacer(1, 20))
    
    # Estatísticas gerais
    story.append(Paragraph("RESUMO EXECUTIVO", heading_style))
    
    # Calcular score médio geral
    scores_gerais = []
    estatisticas_assessments = []
    
    for projeto_assessment in projeto.assessments:
        if not projeto_assessment.finalizado:
            continue
            
        # Determinar tipo e versão do assessment
        tipo = None
        versao_info = "Sistema Antigo"
        
        if projeto_assessment.versao_assessment_id:
            versao = projeto_assessment.versao_assessment
            tipo = versao.tipo
            versao_info = f"Versão {versao.versao}"
        elif projeto_assessment.tipo_assessment_id:
            tipo = projeto_assessment.tipo_assessment
            versao_info = "Sistema Antigo"
        
        if not tipo:
            continue
        
        # Calcular score geral do assessment
        if projeto_assessment.versao_assessment_id:
            score_query = db.session.query(
                func.avg(Resposta.nota).label('score_medio'),
                func.count(Resposta.id).label('total_respostas')
            ).join(
                Pergunta, Resposta.pergunta_id == Pergunta.id
            ).join(
                AssessmentDominio, Pergunta.dominio_versao_id == AssessmentDominio.id
            ).filter(
                Resposta.projeto_id == projeto.id,
                AssessmentDominio.versao_id == versao.id,
                AssessmentDominio.ativo == True,
                Pergunta.ativo == True
            ).first()
        else:
            score_query = db.session.query(
                func.avg(Resposta.nota).label('score_medio'),
                func.count(Resposta.id).label('total_respostas')
            ).join(
                Pergunta, Resposta.pergunta_id == Pergunta.id
            ).join(
                Dominio, Pergunta.dominio_id == Dominio.id
            ).filter(
                Resposta.projeto_id == projeto.id,
                Dominio.tipo_assessment_id == tipo.id,
                Dominio.ativo == True,
                Pergunta.ativo == True
            ).first()
        
        score_geral = round(float(score_query.score_medio or 0), 2)
        total_respostas = score_query.total_respostas or 0
        
        scores_gerais.append(score_geral)
        estatisticas_assessments.append({
            'tipo': tipo,
            'versao_info': versao_info,
            'score_geral': score_geral,
            'total_respostas': total_respostas,
            'data_finalizacao': projeto_assessment.data_finalizacao
        })
    
    score_medio_projeto = round(sum(scores_gerais) / len(scores_gerais) if scores_gerais else 0, 2)
    
    # Tabela de resumo
    resumo_data = [
        ['Métrica', 'Valor'],
        ['Score Médio Geral', f'{score_medio_projeto}/5.0'],
        ['Total de Assessments', str(len(estatisticas_assessments))],
        ['Total de Respondentes', str(len(projeto.get_respondentes_ativos()))],
        ['Data de Criação', projeto.data_criacao.strftime('%d/%m/%Y')],
    ]
    
    # Encontrar data de finalização mais recente
    data_finalizacao = None
    for assessment in estatisticas_assessments:
        if assessment['data_finalizacao']:
            if not data_finalizacao or assessment['data_finalizacao'] > data_finalizacao:
                data_finalizacao = assessment['data_finalizacao']
    
    if data_finalizacao:
        resumo_data.append(['Data de Finalização', data_finalizacao.strftime('%d/%m/%Y')])
    
    resumo_table = Table(resumo_data, colWidths=[3*inch, 2*inch])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resumo_table)
    story.append(Spacer(1, 20))
    
    # Detalhamento por assessment
    for assessment in estatisticas_assessments:
        story.append(Paragraph(f"ASSESSMENT: {assessment['tipo'].nome}", heading_style))
        story.append(Paragraph(f"{assessment['versao_info']} - Score: {assessment['score_geral']}/5.0", subheading_style))
        
        # Buscar domínios e suas estatísticas
        if projeto.assessments[0].versao_assessment_id:
            versao = projeto.assessments[0].versao_assessment
            dominios_query = AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True)
        else:
            dominios_query = Dominio.query.filter_by(tipo_assessment_id=assessment['tipo'].id, ativo=True)
        
        dominios_data = [['Domínio', 'Score', 'Nível de Maturidade']]
        
        for dominio in dominios_query.order_by('ordem'):
            if projeto.assessments[0].versao_assessment_id:
                dominio_score_query = db.session.query(
                    func.avg(Resposta.nota).label('score_medio')
                ).join(
                    Pergunta, Resposta.pergunta_id == Pergunta.id
                ).filter(
                    Resposta.projeto_id == projeto.id,
                    Pergunta.dominio_versao_id == dominio.id,
                    Pergunta.ativo == True
                ).first()
            else:
                dominio_score_query = db.session.query(
                    func.avg(Resposta.nota).label('score_medio')
                ).join(
                    Pergunta, Resposta.pergunta_id == Pergunta.id
                ).filter(
                    Resposta.projeto_id == projeto.id,
                    Pergunta.dominio_id == dominio.id,
                    Pergunta.ativo == True
                ).first()
            
            dominio_score = round(float(dominio_score_query.score_medio or 0), 2)
            
            # Determinar nível de maturidade
            if dominio_score >= 4.5:
                nivel_maturidade = "Otimizado"
            elif dominio_score >= 3.5:
                nivel_maturidade = "Avançado"
            elif dominio_score >= 2.5:
                nivel_maturidade = "Intermediário"
            elif dominio_score >= 1.5:
                nivel_maturidade = "Básico"
            elif dominio_score >= 0.5:
                nivel_maturidade = "Inicial"
            else:
                nivel_maturidade = "Inexistente"
            
            dominios_data.append([
                dominio.nome,
                f'{dominio_score}/5.0',
                nivel_maturidade
            ])
        
        dominios_table = Table(dominios_data, colWidths=[3*inch, 1*inch, 1.5*inch])
        dominios_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(dominios_table)
        story.append(Spacer(1, 20))
    
    # Memorial de respostas
    story.append(PageBreak())
    story.append(Paragraph("MEMORIAL DE RESPOSTAS E COMENTÁRIOS", heading_style))
    
    # Coletar memorial de respostas
    for projeto_assessment in projeto.assessments:
        if not projeto_assessment.finalizado:
            continue
            
        # Determinar tipo e versão do assessment
        tipo = None
        if projeto_assessment.versao_assessment_id:
            versao = projeto_assessment.versao_assessment
            tipo = versao.tipo
            dominios_query = AssessmentDominio.query.filter_by(versao_id=versao.id, ativo=True)
        elif projeto_assessment.tipo_assessment_id:
            tipo = projeto_assessment.tipo_assessment
            dominios_query = Dominio.query.filter_by(tipo_assessment_id=tipo.id, ativo=True)
        
        if not tipo:
            continue
        
        story.append(Paragraph(f"Assessment: {tipo.nome}", subheading_style))
        
        for dominio in dominios_query.order_by('ordem'):
            story.append(Paragraph(f"Domínio: {dominio.nome}", subheading_style))
            
            # Coletar perguntas e respostas do domínio
            if projeto_assessment.versao_assessment_id:
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
                # Buscar resposta mais recente desta pergunta no projeto
                resposta = Resposta.query.filter_by(
                    projeto_id=projeto.id,
                    pergunta_id=pergunta.id
                ).order_by(Resposta.data_resposta.desc()).first()
                
                if resposta:
                    story.append(Paragraph(f"<b>Pergunta:</b> {pergunta.texto}", normal_style))
                    story.append(Paragraph(f"<b>Nota:</b> {resposta.nota}/5", normal_style))
                    
                    if resposta.comentario:
                        story.append(Paragraph(f"<b>Comentário:</b> {resposta.comentario}", normal_style))
                    else:
                        story.append(Paragraph("<b>Comentário:</b> Nenhum comentário fornecido", normal_style))
                    
                    respondente_nome = resposta.respondente.nome if resposta.respondente else 'Sistema'
                    data_resposta = resposta.data_resposta.strftime('%d/%m/%Y às %H:%M')
                    story.append(Paragraph(f"<b>Respondente:</b> {respondente_nome} - {data_resposta}", normal_style))
                    story.append(Spacer(1, 10))
            
            story.append(Spacer(1, 15))
    
    # CTA de Contato
    story.append(PageBreak())
    
    # Buscar tipo de assessment do projeto para pegar o CTA personalizado
    tipo_assessment = None
    for projeto_assessment in projeto.assessments:
        if projeto_assessment.versao_assessment_id:
            tipo_assessment = projeto_assessment.versao_assessment.tipo
            break
        elif projeto_assessment.tipo_assessment_id:
            tipo_assessment = projeto_assessment.tipo_assessment
            break
    
    # Criar um box de destaque para o CTA
    cta_style = ParagraphStyle(
        'CTAStyle',
        parent=normal_style,
        fontSize=12,
        textColor=colors.HexColor('#0f4c75'),
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=18
    )
    
    cta_title_style = ParagraphStyle(
        'CTATitleStyle',
        parent=heading_style,
        fontSize=18,
        textColor=colors.HexColor('#4CAF50'),
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    # Usar CTA personalizado se existir, senão usar padrão
    if tipo_assessment and tipo_assessment.cta_texto:
        # CTA personalizado - usar pre-line para manter quebras de linha
        cta_paragrafos = tipo_assessment.cta_texto.strip().split('\n')
        for paragrafo in cta_paragrafos:
            if paragrafo.strip():
                story.append(Paragraph(paragrafo, cta_style))
    else:
        # CTA padrão
        story.append(Paragraph("QUER MELHORAR SEUS RESULTADOS?", cta_title_style))
        cta_text = """
        A <b>Gruppen</b> e suas empresas especializadas podem ajudar você a evoluir 
        nos controles deste assessment. Entre em contato conosco agora mesmo!
        """
        story.append(Paragraph(cta_text, cta_style))
    
    story.append(Spacer(1, 15))
    
    # Dados de contato em tabela
    contato_data = [
        ['Canal', 'Contato'],
        ['WhatsApp', '(51) 98968-3228'],
        ['E-mail', 'comercial@gruppen.com.br'],
        ['Website', 'www.gruppen.com.br']
    ]
    
    contato_table = Table(contato_data, colWidths=[2*inch, 4*inch])
    contato_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8f5e9')),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#4CAF50')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10)
    ]))
    
    story.append(contato_table)
    story.append(Spacer(1, 30))
    
    # Legenda de níveis de maturidade
    story.append(PageBreak())
    story.append(Paragraph("LEGENDA - NÍVEIS DE MATURIDADE", heading_style))
    
    legenda_data = [
        ['Faixa de Score', 'Nível', 'Descrição'],
        ['0.0 - 0.5', 'Inexistente', 'Nenhum controle implementado'],
        ['0.5 - 1.5', 'Inicial', 'Práticas informais e não documentadas'],
        ['1.5 - 2.5', 'Básico', 'Controles definidos, aplicação inconsistente'],
        ['2.5 - 3.5', 'Intermediário', 'Controles padronizados e repetíveis'],
        ['3.5 - 4.5', 'Avançado', 'Controles monitorados com métricas'],
        ['4.5 - 5.0', 'Otimizado', 'Controles integrados e melhorados continuamente']
    ]
    
    legenda_table = Table(legenda_data, colWidths=[1.2*inch, 1.5*inch, 3.3*inch])
    legenda_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(legenda_table)
    
    # Construir documento
    doc.build(story)
    
    return temp_filename

def allowed_file(filename, allowed_extensions):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions