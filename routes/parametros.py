"""
Rotas para gerenciamento de parâmetros do sistema
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import db
from utils.auth_utils import admin_required
from models.parametro_sistema import ParametroSistema
from forms.parametro_forms import ParametroSistemaForm, OpenAIConfigForm, AparenciaForm
from models.logo import Logo
from forms.admin_forms import LogoForm

parametros_bp = Blueprint('parametros', __name__, url_prefix='/admin/parametros')

@parametros_bp.route('/')
@login_required
@admin_required
def listar():
    """Página principal de parâmetros do sistema"""
    
    # Formulários
    parametro_form = ParametroSistemaForm()
    openai_form = OpenAIConfigForm()
    
    # Carregar valores atuais
    parametro_form.fuso_horario.data = ParametroSistema.get_valor('fuso_horario', 'America/Sao_Paulo')
    
    # Carregar configurações OpenAI
    openai_config = ParametroSistema.get_openai_config()
    openai_form.openai_assistant_name.data = openai_config['assistant_name']
    # Não carregamos a API key por segurança
    
    return render_template('admin/parametros/index.html',
                         parametro_form=parametro_form,
                         openai_form=openai_form,
                         openai_config=openai_config)

@parametros_bp.route('/salvar_geral', methods=['POST'])
@login_required
@admin_required
def salvar_geral():
    """Salva configurações gerais do sistema"""
    form = ParametroSistemaForm()
    
    if form.validate_on_submit():
        try:
            # Salvar fuso horário
            ParametroSistema.set_valor('fuso_horario', form.fuso_horario.data, 'string',
                                     'Fuso horário do sistema', 'geral')
            
            flash('Configurações gerais salvas com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao salvar configurações: {str(e)}', 'danger')
            db.session.rollback()
    else:
        flash('Erro de validação nos dados enviados.', 'danger')
    
    return redirect(url_for('parametros.listar'))

@parametros_bp.route('/salvar_openai', methods=['POST'])
@login_required
@admin_required
def salvar_openai():
    """Salva configurações do OpenAI"""
    form = OpenAIConfigForm()
    
    if form.validate_on_submit():
        try:
            # Salvar configurações OpenAI
            ParametroSistema.set_openai_config(
                form.openai_api_key.data,
                form.openai_assistant_name.data
            )
            
            flash('Configurações do OpenAI salvas com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao salvar configurações do OpenAI: {str(e)}', 'danger')
            db.session.rollback()
    else:
        flash('Erro de validação nos dados enviados.', 'danger')
    
    return redirect(url_for('parametros.listar'))

@parametros_bp.route('/aparencia')
@login_required
@admin_required
def aparencia():
    """Página de configurações de aparência"""
    
    # Formulários
    aparencia_form = AparenciaForm()
    logo_form = LogoForm()
    
    # Logo atual
    try:
        logo_atual = Logo.get_logo_ativo()
    except:
        logo_atual = None
    
    # Carregar cores atuais
    try:
        from models.configuracao import Configuracao
        cores = Configuracao.get_cores_sistema()
        aparencia_form.cor_primaria.data = cores.get('primaria', '#0d6efd')
        aparencia_form.cor_secundaria.data = cores.get('secundaria', '#6c757d')
        aparencia_form.cor_fundo.data = cores.get('fundo', '#ffffff')
        aparencia_form.cor_texto.data = cores.get('texto', '#212529')
    except:
        # Usar valores padrão se não houver configurações
        pass
    
    return render_template('admin/parametros/aparencia.html',
                         aparencia_form=aparencia_form,
                         logo_form=logo_form,
                         logo_atual=logo_atual)

@parametros_bp.route('/salvar_aparencia', methods=['POST'])
@login_required
@admin_required
def salvar_aparencia():
    """Salva configurações de aparência"""
    form = AparenciaForm()
    
    if form.validate_on_submit():
        try:
            from models.configuracao import Configuracao
            
            # Salvar cores
            cores = {
                'primaria': form.cor_primaria.data,
                'secundaria': form.cor_secundaria.data,
                'fundo': form.cor_fundo.data,
                'texto': form.cor_texto.data
            }
            
            Configuracao.set_cores_sistema(cores)
            
            flash('Configurações de aparência salvas com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao salvar configurações de aparência: {str(e)}', 'danger')
            db.session.rollback()
    else:
        flash('Erro de validação nos dados enviados.', 'danger')
    
    return redirect(url_for('parametros.aparencia'))

@parametros_bp.route('/upload_logo', methods=['POST'])
@login_required
@admin_required
def upload_logo():
    """Upload de logo do sistema"""
    from utils.upload_utils import salvar_logo
    
    form = LogoForm()
    
    if form.validate_on_submit():
        try:
            arquivo = form.arquivo.data
            if arquivo and arquivo.filename:
                logo = salvar_logo(arquivo)
                flash('Logo atualizado com sucesso!', 'success')
            else:
                flash('Nenhum arquivo selecionado.', 'warning')
        except Exception as e:
            flash(f'Erro ao fazer upload do logo: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {field}: {error}', 'danger')
    
    return redirect(url_for('parametros.aparencia'))