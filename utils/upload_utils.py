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
    from models.logo import Logo
    from app import db
    import logging
    
    try:
        # Salvar arquivo
        logo_path = save_uploaded_file(file, 'logos')
        logging.info(f"Arquivo de logo salvo em: {logo_path}")
        
        # 1. Atualizar configuração do sistema (método principal)
        Configuracao.set_logo_sistema(logo_path)
        logging.info("Logo atualizado na configuração do sistema")
        
        # 2. Desativar todos os logos antigos no modelo Logo
        Logo.query.update({'ativo': False})
        
        # 3. Criar novo registro no modelo Logo
        novo_logo = Logo(
            nome_original=file.filename,
            caminho_arquivo=logo_path,
            ativo=True
        )
        db.session.add(novo_logo)
        
        # 4. Commit das mudanças
        db.session.commit()
        logging.info("Logo salvo com sucesso no banco de dados")
        
        return logo_path
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar logo: {e}")
        raise e
