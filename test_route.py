"""Teste para rota estatísticas simplificada"""

from flask import Blueprint, render_template
from flask_login import login_required
from utils.auth_utils import admin_required
from models.projeto import Projeto

def test_estatisticas(projeto_id):
    try:
        projeto = Projeto.query.get_or_404(projeto_id)
        
        # Dados mínimos
        estatisticas_gerais = {
            'total_respondentes': 0,
            'total_assessments': 0,
            'data_inicio': projeto.data_criacao,
            'data_finalizacao': projeto.data_finalizacao
        }
        
        return render_template('admin/projetos/estatisticas.html',
                             projeto=projeto,
                             estatisticas_gerais=estatisticas_gerais,
                             estatisticas_assessments=[],
                             score_medio_projeto=0,
                             respondentes=[],
                             dados_graficos={'radar': {}, 'scores_assessments': {}},
                             memorial_respostas={},
                             relatorio_ia=None)
    except Exception as e:
        return f"Erro: {str(e)}"