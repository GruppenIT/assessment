from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime
from models.usuario import Usuario
from models.resposta import Resposta
from models.pergunta import Pergunta
from models.dominio import Dominio

def gerar_pdf_relatorio(usuario_id):
    """Gera relatório em PDF para um usuário"""
    buffer = BytesIO()
    
    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Buscar dados
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        raise ValueError("Usuário não encontrado")
    
    # Buscar respostas
    respostas = Resposta.query.filter_by(usuario_id=usuario_id).join(
        Pergunta
    ).join(Dominio).order_by(
        Dominio.ordem, Pergunta.ordem
    ).all()
    
    # Organizar dados por domínio
    dados_dominios = {}
    for resposta in respostas:
        dominio_nome = resposta.pergunta.dominio.nome
        
        if dominio_nome not in dados_dominios:
            dados_dominios[dominio_nome] = {
                'respostas': [],
                'notas': []
            }
        
        dados_dominios[dominio_nome]['respostas'].append(resposta)
        dados_dominios[dominio_nome]['notas'].append(resposta.nota)
    
    # Calcular médias
    for dominio_nome, dados in dados_dominios.items():
        if dados['notas']:
            dados['media'] = round(sum(dados['notas']) / len(dados['notas']), 2)
        else:
            dados['media'] = 0
    
    # Média geral
    todas_notas = [resposta.nota for resposta in respostas]
    media_geral = round(sum(todas_notas) / len(todas_notas), 2) if todas_notas else 0
    
    # Estilos
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#007BFF')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#007BFF')
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    
    # Conteúdo do documento
    story = []
    
    # Título
    story.append(Paragraph("Relatório de Assessment de Cibersegurança", title_style))
    story.append(Spacer(1, 12))
    
    # Informações da empresa
    story.append(Paragraph("Informações da Empresa", heading_style))
    
    empresa_data = [
        ['Empresa:', usuario.nome_empresa or 'N/A'],
        ['Responsável:', usuario.nome],
        ['Email:', usuario.email],
        ['Data do Relatório:', datetime.now().strftime('%d/%m/%Y às %H:%M')]
    ]
    
    empresa_table = Table(empresa_data, colWidths=[2*inch, 4*inch])
    empresa_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
    ]))
    
    story.append(empresa_table)
    story.append(Spacer(1, 20))
    
    # Resumo Executivo
    story.append(Paragraph("Resumo Executivo", heading_style))
    
    resumo_data = [
        ['Total de Domínios Avaliados:', str(len(dados_dominios))],
        ['Total de Perguntas Respondidas:', str(len(respostas))],
        ['Pontuação Geral:', f"{media_geral}/5.0"],
        ['Percentual Geral:', f"{(media_geral/5)*100:.1f}%"]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[3*inch, 2*inch])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
    ]))
    
    story.append(resumo_table)
    story.append(Spacer(1, 20))
    
    # Pontuação por Domínio
    story.append(Paragraph("Pontuação por Domínio", heading_style))
    
    dominios_data = [['Domínio', 'Pontuação Média', 'Percentual']]
    
    for dominio_nome, dados in dados_dominios.items():
        media = dados['media']
        percentual = (media/5)*100
        dominios_data.append([dominio_nome, f"{media}/5.0", f"{percentual:.1f}%"])
    
    dominios_table = Table(dominios_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    dominios_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007BFF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
    ]))
    
    story.append(dominios_table)
    story.append(Spacer(1, 20))
    
    # Detalhamento por Domínio
    for dominio_nome, dados in dados_dominios.items():
        story.append(Paragraph(f"Detalhamento: {dominio_nome}", heading_style))
        
        # Criar tabela de respostas do domínio
        respostas_data = [['Pergunta', 'Nota', 'Comentário']]
        
        for resposta in dados['respostas']:
            pergunta_texto = resposta.pergunta.texto[:100] + "..." if len(resposta.pergunta.texto) > 100 else resposta.pergunta.texto
            comentario = resposta.comentario[:150] + "..." if resposta.comentario and len(resposta.comentario) > 150 else (resposta.comentario or "Sem comentário")
            
            respostas_data.append([
                pergunta_texto,
                f"{resposta.nota}/5",
                comentario
            ])
        
        respostas_table = Table(respostas_data, colWidths=[3*inch, 1*inch, 2*inch])
        respostas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
        ]))
        
        story.append(respostas_table)
        story.append(Spacer(1, 15))
    
    # Rodapé
    story.append(Spacer(1, 30))
    rodape_style = ParagraphStyle(
        'Rodape',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#6c757d')
    )
    
    story.append(Paragraph(
        f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | Sistema de Assessment de Cibersegurança",
        rodape_style
    ))
    
    # Construir PDF
    doc.build(story)
    
    # Obter conteúdo do buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
