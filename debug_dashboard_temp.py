#!/usr/bin/env python3
"""
Função de dashboard temporária simplificada para debug
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import render_template
from flask_login import login_required, current_user
from app import create_app, db
from models.cliente import Cliente
from models.respondente import Respondente
from models.projeto import Projeto
from models.assessment_version import AssessmentTipo
from models.resposta import Resposta
from utils.auth_utils import admin_required

def dashboard_simples():
    """Dashboard simplificado para identificar problema"""
    try:
        print("🔍 DEBUG: Iniciando dashboard simplificado")
        
        # Stats mínimas
        stats = {
            'total_clientes': Cliente.query.filter_by(ativo=True).count(),
            'total_respondentes': Respondente.query.filter_by(ativo=True).count(),
            'total_projetos': Projeto.query.filter_by(ativo=True).count(),
            'total_tipos': AssessmentTipo.query.filter_by(ativo=True).count(),
            'total_respostas': Resposta.query.count()
        }
        
        print(f"✅ DEBUG: Stats calculadas: {stats}")
        
        return render_template('admin/dashboard.html',
                             momento_do_dia="Olá",
                             stats=stats,
                             atividade_diaria=[],
                             projetos_detalhados=[],
                             tipos_stats=[],
                             clientes_detalhados=[],
                             alertas=[],
                             atividades_recentes=[])
        
    except Exception as e:
        print(f"❌ DEBUG: Erro no dashboard: {e}")
        import traceback
        traceback.print_exc()
        return f"Erro: {e}", 500

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        result = dashboard_simples()
        print("✅ Dashboard executado")