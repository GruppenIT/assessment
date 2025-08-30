"""
Utilitários para tratamento seguro de senhas com caracteres especiais
"""

from werkzeug.security import check_password_hash, generate_password_hash
import unicodedata
import html

def normalize_password(password):
    """
    Normaliza senha para evitar problemas de encoding
    """
    if not password:
        return password
    
    try:
        # Converter para string se não for
        if not isinstance(password, str):
            password = str(password)
            
        # Decodificar entities HTML se houver
        password = html.unescape(password)
        
        # Normalizar Unicode (remover acentos e caracteres especiais compostos)
        password = unicodedata.normalize('NFKC', password)
        
        # Garantir UTF-8
        password = password.encode('utf-8').decode('utf-8')
        
        return password
        
    except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
        # Se der algum erro, retornar senha original
        return password

def safe_check_password_hash(password_hash, password):
    """
    Verifica hash de senha de forma segura, tentando diferentes normalizações
    """
    if not password_hash or not password:
        return False
    
    # Lista de tentativas de normalização
    password_variants = [
        password,  # Original
        normalize_password(password),  # Normalizada
        password.strip(),  # Sem espaços
        html.unescape(password),  # Sem HTML entities
    ]
    
    # Remover duplicatas mantendo ordem
    seen = set()
    unique_variants = []
    for variant in password_variants:
        if variant and variant not in seen:
            seen.add(variant)
            unique_variants.append(variant)
    
    # Testar cada variante
    for variant in unique_variants:
        try:
            if check_password_hash(password_hash, variant):
                return True
        except Exception:
            continue
    
    return False

def safe_generate_password_hash(password):
    """
    Gera hash de senha de forma segura
    """
    if not password:
        return None
    
    # Normalizar senha antes de gerar hash
    normalized_password = normalize_password(password)
    
    try:
        return generate_password_hash(normalized_password)
    except Exception as e:
        # Se der erro, tentar com senha original
        return generate_password_hash(password)