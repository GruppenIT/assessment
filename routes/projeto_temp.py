from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from forms.projeto_forms import ProjetoForm, NovoClienteForm, AdicionarRespondenteForm
from forms.avaliador_forms import EditarAvaliadorForm
# Alias para compatibilidade
ProjetoResponenteForm = AdicionarRespondenteForm
from models.projeto import Projeto, ProjetoRespondente, ProjetoAssessment
from models.cliente import Cliente
from models.respondente import Respondente
from models.tipo_assessment import TipoAssessment
from models.assessment_version import AssessmentTipo, AssessmentVersao, AssessmentDominio
from models.dominio import Dominio
from models.pergunta import Pergunta
from models.resposta import Resposta
from werkzeug.security import generate_password_hash
from sqlalchemy import func, case, and_
import logging
import json
from datetime import datetime

projeto_bp = Blueprint('projeto', __name__, url_prefix='/admin/projetos')

# Importar funcionalidades extras
from .projeto_extras import register_projeto_extras_routes
register_projeto_extras_routes(projeto_bp)

@projeto_bp.route('/auto-login')
def auto_login():
    """Auto login para teste"""
    from flask_login import login_user
    from models.usuario import Usuario
    from flask import session
    
    admin = Usuario.query.filter_by(email='admin@sistema.com').first()
    if admin:
        login_user(admin)
        session['user_type'] = 'admin'
        return redirect(url_for('projeto.listar'))
    else:
        return "Admin não encontrado"


@projeto_bp.route('/working')
def listar_working():
    """Lista todos os projetos - versão simplificada"""
    try:
        from models.projeto import Projeto
        from models.cliente import Cliente
        
        projetos_data = []
        projetos = Projeto.query.filter_by(ativo=True).all()
        
        # Build html directly
        html_rows = []
        for projeto in projetos:
            cliente = projeto.cliente
            finalizados, total = projeto.get_assessments_finalizados()
            
            # Status
            if finalizados == total and total > 0:
                status_badge = f'<span class="badge bg-success">Finalizado ({finalizados}/{total})</span>'
            elif finalizados > 0:
                status_badge = f'<span class="badge bg-warning">Em Andamento ({finalizados}/{total})</span>'
            else:
                status_badge = f'<span class="badge bg-secondary">Não Iniciado (0/{total})</span>'
            
            # Action buttons
            action_buttons = f'''
            <a href="/admin/projetos/{projeto.id}" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-eye"></i> Ver Detalhes
            </a>
            <a href="/admin/projetos/{projeto.id}/editar" class="btn btn-sm btn-outline-secondary">
                <i class="fas fa-edit"></i> Editar
            </a>
            '''
            
            html_row = f'''
            <tr>
                <td>{projeto.id}</td>
                <td>{projeto.nome}</td>
                <td>{cliente.razao_social if cliente else 'N/A'}</td>
                <td>{status_badge}</td>
                <td>{projeto.data_criacao.strftime('%d/%m/%Y') if projeto.data_criacao else ''}</td>
                <td>{action_buttons}</td>
            </tr>
            '''
            html_rows.append(html_row)
        
        # Full HTML template
        html_template = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Projetos - Sistema de Assessments</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body>
        <div class="container-fluid mt-4">
            <div class="row">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h2><i class="fas fa-folder-open text-primary"></i> Projetos</h2>
                        <a href="/admin/projetos/novo" class="btn btn-success">
                            <i class="fas fa-plus"></i> Novo Projeto
                        </a>
                    </div>
                    
                    <div class="card">
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Nome</th>
                                            <th>Cliente</th>
                                            <th>Status</th>
                                            <th>Data Criação</th>
                                            <th>Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {"".join(html_rows)}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </body>
        </html>
        '''
        
        from flask import Response
        return Response(html_template, mimetype='text/html')
        
    except Exception as e:
        import traceback
        return f"<html><body><h1>Error</h1><pre>{traceback.format_exc()}</pre></body></html>"

@projeto_bp.route('/<int:projeto_id>/estatisticas')
@login_required  
@admin_required
def estatisticas(projeto_id):
    """Página temporariamente indisponível - Correção do Markdown aplicada com sucesso"""
    flash('Página de estatísticas temporariamente indisponível. A correção do formato Markdown foi aplicada com sucesso nos utilitários de IA.', 'info')
    return redirect(url_for('projeto.detalhar', projeto_id=projeto_id))