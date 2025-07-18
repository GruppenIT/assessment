"""
Utilitários para gerenciamento de timezone
"""

import pytz
from datetime import datetime
from models.parametro_sistema import ParametroSistema

def get_sistema_timezone():
    """Recupera o timezone configurado no sistema"""
    timezone_str = ParametroSistema.get_valor('fuso_horario', 'America/Sao_Paulo')
    return pytz.timezone(timezone_str)

def utc_to_local(utc_datetime):
    """Converte datetime UTC para timezone local do sistema"""
    if not utc_datetime:
        return None
    
    if utc_datetime.tzinfo is None:
        # Assume que é UTC se não tem timezone
        utc_datetime = pytz.utc.localize(utc_datetime)
    
    sistema_tz = get_sistema_timezone()
    return utc_datetime.astimezone(sistema_tz)

def local_to_utc(local_datetime):
    """Converte datetime local para UTC"""
    if not local_datetime:
        return None
    
    sistema_tz = get_sistema_timezone()
    if local_datetime.tzinfo is None:
        # Localizar no timezone do sistema
        local_datetime = sistema_tz.localize(local_datetime)
    
    return local_datetime.astimezone(pytz.utc)

def now_local():
    """Retorna datetime atual no timezone do sistema"""
    return utc_to_local(datetime.utcnow())

def format_datetime_local(utc_datetime, formato='%d/%m/%Y %H:%M'):
    """Formata datetime para exibição no timezone local"""
    if not utc_datetime:
        return ''
    
    local_dt = utc_to_local(utc_datetime)
    return local_dt.strftime(formato)

def format_date_local(utc_datetime, formato='%d/%m/%Y'):
    """Formata data para exibição no timezone local"""
    return format_datetime_local(utc_datetime, formato)

def format_time_local(utc_datetime, formato='%H:%M'):
    """Formata hora para exibição no timezone local"""
    return format_datetime_local(utc_datetime, formato)

def get_timezone_display_name():
    """Retorna o nome amigável do timezone configurado"""
    timezone_mapping = {
        'America/Sao_Paulo': 'Brasil - GMT-3 (Brasília)',
        'America/Fortaleza': 'Brasil - GMT-3 (Fortaleza)',
        'America/Recife': 'Brasil - GMT-3 (Recife)',
        'America/Manaus': 'Brasil - GMT-4 (Manaus)',
        'America/Porto_Velho': 'Brasil - GMT-4 (Porto Velho)',
        'UTC': 'UTC - GMT+0',
        'America/New_York': 'EUA - EST (Nova York)',
        'Europe/London': 'Reino Unido - GMT (Londres)',
        'Europe/Paris': 'França - CET (Paris)',
    }
    
    timezone_str = ParametroSistema.get_valor('fuso_horario', 'America/Sao_Paulo')
    return timezone_mapping.get(timezone_str, timezone_str)