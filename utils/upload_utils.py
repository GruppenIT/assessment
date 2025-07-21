import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, subfolder=''):
    """Salva arquivo com nome único"""
    if not file or not allowed_file(file.filename):
        raise ValueError("Arquivo inválido")
    
    # Gerar nome único
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    # Criar diretório se não existir
    upload_dir = os.path.join('static', 'uploads')
    if subfolder:
        upload_dir = os.path.join(upload_dir, subfolder)
    
    os.makedirs(upload_dir, exist_ok=True)
    
    # Salvar arquivo
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    # Retornar o caminho relativo correto
    if subfolder:
        return os.path.join(subfolder, unique_filename)
    return unique_filename

def delete_file(file_path):
    """Remove arquivo do sistema de arquivos"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False

def get_file_size(file_path):
    """Retorna o tamanho do arquivo em bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception:
        return 0

def salvar_logo(file):
    """Salva logo do sistema"""
    if not file or not allowed_file(file.filename):
        raise ValueError("Arquivo de imagem inválido")
    
    from models.configuracao import Configuracao
    from app import db
    
    # Salvar arquivo
    logo_path = save_uploaded_file(file, 'logos')
    
    # Atualizar configuração do sistema
    Configuracao.set_logo_sistema(logo_path)
    
    return logo_path
