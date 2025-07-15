"""
Utilitário para geração de PDFs do sistema de assessment
"""

import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from models.assessment_version import AssessmentDominio
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from app import db
from sqlalchemy import func

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
                ).order_by(Resposta.data_criacao.desc()).first()
                
                if resposta:
                    story.append(Paragraph(f"<b>Pergunta:</b> {pergunta.texto}", normal_style))
                    story.append(Paragraph(f"<b>Nota:</b> {resposta.nota}/5", normal_style))
                    
                    if resposta.comentario:
                        story.append(Paragraph(f"<b>Comentário:</b> {resposta.comentario}", normal_style))
                    else:
                        story.append(Paragraph("<b>Comentário:</b> Nenhum comentário fornecido", normal_style))
                    
                    respondente_nome = resposta.respondente.nome if resposta.respondente else 'Sistema'
                    data_resposta = resposta.data_criacao.strftime('%d/%m/%Y às %H:%M')
                    story.append(Paragraph(f"<b>Respondente:</b> {respondente_nome} - {data_resposta}", normal_style))
                    story.append(Spacer(1, 10))
            
            story.append(Spacer(1, 15))
    
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