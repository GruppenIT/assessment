#!/usr/bin/env python3
"""
WSGI entry point para o sistema de assessment
Para uso com gunicorn ou outros servidores WSGI
"""

import os
import sys
from app import create_app

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

# Criar a aplicação
application = create_app()

# Para compatibilidade com alguns servidores WSGI
app = application

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)