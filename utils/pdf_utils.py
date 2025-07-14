from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

def gerar_relatorio_pdf(dados):
    """Gera relatório PDF do assessment"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center
    )
    
    story.append(Paragraph("RELATÓRIO DE AVALIAÇÃO DE MATURIDADE", title_style))
    story.append(Spacer(1, 20))
    
    # Informações do cliente
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.darkblue
    )
    
    story.append(Paragraph("INFORMAÇÕES DO CLIENTE", header_style))
    
    # Dados do cliente em tabela
    cliente_data = [
        ['Nome Fantasia:', dados['cliente'].nome],
        ['Razão Social:', dados['cliente'].razao_social],
        ['CNPJ:', dados['cliente'].cnpj or 'N/A'],
        ['Localidade:', dados['cliente'].localidade or 'N/A'],
        ['Segmento:', dados['cliente'].segmento or 'N/A'],
        ['Tipo de Assessment:', dados['tipo_assessment'].nome],
        ['Total de Respondentes:', str(dados['total_respondentes'])],
        ['Data de Geração:', dados['data_geracao'].strftime('%d/%m/%Y às %H:%M')]
    ]
    
    cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(cliente_table)
    story.append(Spacer(1, 20))
    
    # Resumo executivo
    story.append(Paragraph("RESUMO EXECUTIVO", header_style))
    
    resumo_data = [
        ['Média Geral:', f"{dados['media_geral']}/5.0"],
        ['Nível de Maturidade:', dados['nivel_maturidade']],
        ['Total de Respostas:', str(dados['total_respostas'])],
        ['Percentual de Completude:', f"{round((dados['total_respostas'] / (sum(e['total_possivel'] for e in dados['estatisticas_dominios']) or 1)) * 100, 1)}%" if dados['estatisticas_dominios'] else "0%"]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[2*inch, 4*inch])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (1, 0), (1, -1), colors.lightcyan),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resumo_table)
    story.append(Spacer(1, 20))
    
    # Estatísticas por domínio
    story.append(Paragraph("RESULTADOS POR DOMÍNIO", header_style))
    
    if dados['estatisticas_dominios']:
        dominio_data = [['Domínio', 'Média', 'Respostas', 'Completude']]
        
        for est in dados['estatisticas_dominios']:
            dominio_data.append([
                est['dominio'].nome,
                f"{est['media']}/5.0",
                f"{est['respondidas']}/{est['total_possivel']}",
                f"{est['percentual_completude']}%"
            ])
        
        dominio_table = Table(dominio_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1*inch])
        dominio_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(dominio_table)
    else:
        story.append(Paragraph("Nenhum domínio avaliado.", styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Escala de maturidade
    story.append(Paragraph("ESCALA DE MATURIDADE", header_style))
    
    escala_data = [
        ['Nível', 'Descrição'],
        ['5 - Otimizado', 'Controles integrados e melhorados continuamente'],
        ['4 - Avançado', 'Controles monitorados com métricas'],
        ['3 - Intermediário', 'Controles padronizados e repetíveis'],
        ['2 - Básico', 'Controles definidos, aplicação inconsistente'],
        ['1 - Inicial', 'Práticas informais e não documentadas'],
        ['0 - Inexistente', 'Nenhum controle implementado']
    ]
    
    escala_table = Table(escala_data, colWidths=[1.5*inch, 4.5*inch])
    escala_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(escala_table)
    story.append(Spacer(1, 20))
    
    # Rodapé
    story.append(Spacer(1, 40))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1  # Center
    )
    
    story.append(Paragraph("Relatório gerado pelo Sistema de Avaliações de Maturidade", footer_style))
    story.append(Paragraph("© Gruppen Serviços de Informática Ltda", footer_style))
    
    # Gerar PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    
    return pdf_value