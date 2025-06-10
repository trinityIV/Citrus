"""
Script de lancement de Citrus Music Server en mode production
"""

from src import create_app

if __name__ == '__main__':
    app = create_app('production')
    app.run(host='0.0.0.0', port=5000, debug=False)
