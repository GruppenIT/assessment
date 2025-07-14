from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import tempfile

def gerar_grafico_radar(dados):
    """Gera gráfico radar com os dados dos domínios"""
    # Configurar matplotlib para não usar display
    import matplotlib
    matplotlib.use('Agg')  # Use backend sem display
    
    # Preparar dados para o gráfico radar
    dominios = []
    valores = []
    
    for est in dados['estatisticas_dominios']:
        dominios.append(est['dominio'].nome)
        valores.append(est['media'])
    
    # Se não houver dados, retornar None
    if not dominios:
        return None
    
    # Configurar o gráfico
    N = len(dominios)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    valores += valores[:1]  # Fechar o polígono
    angles += angles[:1]    # Fechar o polígono
    
    # Criar figura
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # Plotar o gráfico radar
    ax.plot(angles, valores, 'o-', linewidth=2, label='Pontuação por Domínio', color='#1f77b4')
    ax.fill(angles, valores, alpha=0.25, color='#1f77b4')
    
    # Configurar o gráfico
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dominios, fontsize=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=8)
    ax.grid(True)
    
    # Adicionar linhas de referência
    ax.axhline(y=1, color='red', linestyle='--', alpha=0.5, label='Inicial')
    ax.axhline(y=2, color='orange', linestyle='--', alpha=0.5, label='Básico')
    ax.axhline(y=3, color='yellow', linestyle='--', alpha=0.5, label='Intermediário')
    ax.axhline(y=4, color='lightgreen', linestyle='--', alpha=0.5, label='Avançado')
    ax.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='Otimizado')
    
    plt.title('Gráfico Radar - Avaliação por Domínio', size=16, weight='bold', pad=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
    
    # Salvar em arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    plt.savefig(temp_file.name, dpi=300, bbox_inches='tight')
    plt.close()
    
    return temp_file.name

def gerar_relatorio_pdf(dados):
    """Gera relatório PDF do assessment"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Título principal
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=20,
        textColor=colors.darkblue,
        alignment=1  # Center
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center
    )
    
    story.append(Paragraph("RELATÓRIO DE AVALIAÇÃO DE MATURIDADE", title_style))
    story.append(Paragraph(f"Assessment: {dados['tipo_assessment'].nome}", subtitle_style))
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
    
    # Descrição do Assessment
    story.append(Paragraph("SOBRE O ASSESSMENT", header_style))
    
    descricao_assessment = f"""
    <b>Tipo:</b> {dados['tipo_assessment'].nome}<br/>
    <b>Descrição:</b> {dados['tipo_assessment'].descricao or 'Este assessment avalia a maturidade organizacional através de múltiplos domínios.'}<br/>
    <b>Total de Domínios:</b> {len(dados['estatisticas_dominios'])}<br/>
    <b>Metodologia:</b> Avaliação baseada em escala de 0 a 5, onde cada nível representa um grau específico de maturidade organizacional.
    """
    
    story.append(Paragraph(descricao_assessment, styles['Normal']))
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
    
    # Gráfico Radar
    story.append(Paragraph("GRÁFICO RADAR - VISÃO GERAL", header_style))
    
    # Gerar gráfico radar
    grafico_path = gerar_grafico_radar(dados)
    if grafico_path:
        # Adicionar gráfico ao PDF
        radar_img = Image(grafico_path, width=5*inch, height=5*inch)
        story.append(radar_img)
        story.append(Spacer(1, 10))
        
        # Interpretar gráfico
        interpretacao = """
        <b>Interpretação do Gráfico Radar:</b><br/>
        O gráfico radar apresenta a pontuação média de cada domínio avaliado. Quanto mais próximo do centro (0), 
        menor a maturidade. Quanto mais próximo da borda externa (5), maior a maturidade. 
        A área preenchida representa o perfil geral de maturidade da organização.
        """
        story.append(Paragraph(interpretacao, styles['Normal']))
        
        # Limpar arquivo temporário
        try:
            os.unlink(grafico_path)
        except:
            pass
    
    story.append(Spacer(1, 20))
    
    # Análise Detalhada por Domínio
    story.append(Paragraph("ANÁLISE DETALHADA POR DOMÍNIO", header_style))
    
    if dados['estatisticas_dominios']:
        # Tabela resumo dos domínios
        dominio_data = [['Domínio', 'Média', 'Nível', 'Respostas', 'Completude']]
        
        for est in dados['estatisticas_dominios']:
            nivel = calcular_nivel_maturidade(est['media'])
            dominio_data.append([
                est['dominio'].nome,
                f"{est['media']}/5.0",
                nivel.split(' ')[0],  # Apenas o nível
                f"{est['respondidas']}/{est['total_possivel']}",
                f"{est['percentual_completude']}%"
            ])
        
        dominio_table = Table(dominio_data, colWidths=[2*inch, 0.8*inch, 1.2*inch, 1*inch, 1*inch])
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
        story.append(Spacer(1, 20))
        
        # Análise detalhada de cada domínio
        for est in dados['estatisticas_dominios']:
            dominio_title = ParagraphStyle(
                'DominioTitle',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=10,
                textColor=colors.darkblue,
                leftIndent=20
            )
            
            story.append(Paragraph(f"• {est['dominio'].nome}", dominio_title))
            
            # Informações do domínio
            descricao_dominio = f"""
            <b>Descrição:</b> {est['dominio'].descricao or 'Domínio de avaliação de maturidade organizacional.'}<br/>
            <b>Pontuação Média:</b> {est['media']}/5.0<br/>
            <b>Nível de Maturidade:</b> {calcular_nivel_maturidade(est['media'])}<br/>
            <b>Total de Perguntas:</b> {est['dominio'].contar_perguntas()}<br/>
            <b>Respostas Coletadas:</b> {est['respondidas']} de {est['total_possivel']} possíveis<br/>
            <b>Percentual de Completude:</b> {est['percentual_completude']}%
            """
            
            detail_style = ParagraphStyle(
                'Detail',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=40,
                spaceAfter=10
            )
            
            story.append(Paragraph(descricao_dominio, detail_style))
            
            # Análise de desempenho
            if est['media'] >= 4:
                analise = "<b>Análise:</b> Excelente desempenho! Este domínio apresenta alta maturidade organizacional."
            elif est['media'] >= 3:
                analise = "<b>Análise:</b> Bom desempenho. Há oportunidades para melhorias incrementais."
            elif est['media'] >= 2:
                analise = "<b>Análise:</b> Desempenho moderado. Recomenda-se priorizar melhorias neste domínio."
            else:
                analise = "<b>Análise:</b> Necessita atenção urgente. Este domínio requer investimento significativo."
            
            story.append(Paragraph(analise, detail_style))
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("Nenhum domínio avaliado.", styles['Normal']))
    
    story.append(PageBreak())
    
    # Recomendações
    story.append(Paragraph("RECOMENDAÇÕES E PRÓXIMOS PASSOS", header_style))
    
    # Analisar e gerar recomendações baseadas na média geral
    if dados['media_geral'] >= 4:
        recomendacoes = """
        <b>Situação Atual:</b> Excelente nível de maturidade organizacional.<br/><br/>
        <b>Recomendações Prioritárias:</b><br/>
        • Manter os controles atuais e buscar melhorias contínuas<br/>
        • Implementar processos de monitoramento e otimização<br/>
        • Compartilhar boas práticas com outras organizações<br/>
        • Investir em inovação e tecnologias emergentes<br/><br/>
        <b>Próximos Passos:</b><br/>
        • Revisar e atualizar políticas regularmente<br/>
        • Estabelecer métricas avançadas de performance<br/>
        • Considerar certificações e padrões internacionais
        """
    elif dados['media_geral'] >= 3:
        recomendacoes = """
        <b>Situação Atual:</b> Bom nível de maturidade com oportunidades claras de melhoria.<br/><br/>
        <b>Recomendações Prioritárias:</b><br/>
        • Focar nos domínios com pontuação mais baixa<br/>
        • Implementar processos de monitoramento contínuo<br/>
        • Investir em treinamento e capacitação das equipes<br/>
        • Estabelecer métricas de controle e acompanhamento<br/><br/>
        <b>Próximos Passos:</b><br/>
        • Criar plano de ação específico para cada domínio<br/>
        • Definir responsáveis e prazos para implementação<br/>
        • Estabelecer ciclo de revisão e melhoria contínua
        """
    elif dados['media_geral'] >= 2:
        recomendacoes = """
        <b>Situação Atual:</b> Nível básico de maturidade - necessita melhorias estruturais.<br/><br/>
        <b>Recomendações Prioritárias:</b><br/>
        • Priorizar domínios com pontuação mais crítica<br/>
        • Implementar controles básicos de forma consistente<br/>
        • Investir significativamente em capacitação<br/>
        • Estabelecer processos documentados e padronizados<br/><br/>
        <b>Próximos Passos:</b><br/>
        • Elaborar plano de melhoria com cronograma detalhado<br/>
        • Alocar recursos específicos para cada domínio<br/>
        • Implementar controles de acompanhamento rigorosos
        """
    else:
        recomendacoes = """
        <b>Situação Atual:</b> Nível crítico - requer atenção e investimento urgente.<br/><br/>
        <b>Recomendações Prioritárias:</b><br/>
        • Implementar plano de ação imediato e abrangente<br/>
        • Priorizar domínios com maior impacto no negócio<br/>
        • Investir em consultoria especializada<br/>
        • Estabelecer governança e controles básicos<br/><br/>
        <b>Próximos Passos:</b><br/>
        • Criar comitê de melhoria com patrocínio executivo<br/>
        • Definir metas e indicadores de progresso<br/>
        • Implementar ciclo curto de avaliação e correção
        """
    
    story.append(Paragraph(recomendacoes, styles['Normal']))
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
    
    # Informações Adicionais
    story.append(Paragraph("INFORMAÇÕES ADICIONAIS", header_style))
    
    info_adicional = f"""
    <b>Período de Avaliação:</b> {dados['data_geracao'].strftime('%d/%m/%Y')}<br/>
    <b>Respondentes Participantes:</b> {dados['total_respondentes']}<br/>
    <b>Total de Respostas Coletadas:</b> {dados['total_respostas']}<br/>
    <b>Metodologia:</b> Avaliação quantitativa baseada em escala Likert de 6 pontos (0-5)<br/>
    <b>Validade:</b> Este relatório reflete o estado atual da organização na data de geração<br/>
    <b>Recomendação:</b> Reavaliar periodicamente para acompanhar evolução da maturidade
    """
    
    story.append(Paragraph(info_adicional, styles['Normal']))
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
    story.append(Paragraph(f"Gerado em: {dados['data_geracao'].strftime('%d/%m/%Y às %H:%M:%S')}", footer_style))
    
    # Gerar PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    
    return pdf_value

def calcular_nivel_maturidade(media):
    """Calcula o nível de maturidade baseado na média"""
    if media >= 4.5:
        return "Otimizado (Nível 5)"
    elif media >= 3.5:
        return "Avançado (Nível 4)"
    elif media >= 2.5:
        return "Intermediário (Nível 3)"
    elif media >= 1.5:
        return "Básico (Nível 2)"
    elif media >= 0.5:
        return "Inicial (Nível 1)"
    else:
        return "Inexistente (Nível 0)"