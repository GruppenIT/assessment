"""
Portal do cliente para visualização de estatísticas dos projetos liberados
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models.projeto import Projeto
from models.cliente import Cliente
from models.usuario import Usuario
# from utils.auth_utils import login_required  # Não precisa para portal do cliente
from sqlalchemy import func, case
import json
from datetime import datetime
import pytz

cliente_portal_bp = Blueprint('cliente_portal', __name__, url_prefix='/cliente')

@cliente_portal_bp.route('/projetos/<int:projeto_id>/estatisticas')
def estatisticas_cliente(projeto_id):
    """Página de estatísticas para o cliente - somente projetos liberados"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se projeto foi liberado para cliente
    if not projeto.liberado_cliente:
        flash('Este projeto ainda não foi liberado para visualização.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Carregar dados das estatísticas
    try:
        from routes.projeto import calcular_estatisticas_projeto
        (score_medio_projeto, estatisticas_gerais, scores_por_assessment,
         detalhamento_dominio, respondentes_stats, memorial_respostas) = calcular_estatisticas_projeto(projeto)
        
        # Timezone para data/hora
        timezone = pytz.timezone('America/Sao_Paulo')
        data_atual = datetime.now(timezone)
        
        return render_template('cliente/estatisticas_cliente.html',
                             projeto=projeto,
                             score_medio_projeto=score_medio_projeto,
                             estatisticas_gerais=estatisticas_gerais,
                             scores_por_assessment=scores_por_assessment,
                             detalhamento_dominio=detalhamento_dominio,
                             respondentes_stats=respondentes_stats,
                             memorial_respostas=memorial_respostas,
                             data_visualizacao=data_atual.strftime('%d/%m/%Y às %H:%M'))
                             
    except Exception as e:
        flash(f'Erro ao carregar estatísticas: {str(e)}', 'error')
        return redirect(url_for('auth.login'))

@cliente_portal_bp.route('/projetos/<int:projeto_id>/relatorio-pdf')
def gerar_relatorio_cliente(projeto_id):
    """Gera relatório PDF para cliente"""
    projeto = Projeto.query.get_or_404(projeto_id)
    
    # Verificar se projeto foi liberado para cliente
    if not projeto.liberado_cliente:
        flash('Este projeto ainda não foi liberado para visualização.', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        from utils.pdf_relatorio import gerar_relatorio_completo_pdf
        
        pdf_buffer = gerar_relatorio_completo_pdf(projeto)
        
        from flask import make_response
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Relatorio_Assessment_{projeto.nome}_{projeto.cliente.nome}.pdf"'
        
        return response
        
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'error')
        return redirect(url_for('cliente_portal.estatisticas_cliente', projeto_id=projeto_id))