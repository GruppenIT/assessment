# Carregar variáveis de ambiente do .env
import env_loader

from app import create_app

# Criar a aplicação usando o factory pattern
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
