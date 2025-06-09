import os
import sys
import time
import requests
import subprocess
import psutil
from config.logging_config import setup_logging

# Configuration du logger
logger = setup_logging()

class CitrusServerTester:
    def __init__(self, host='192.168.0.181', port=5000):
        self.host = host
        self.port = port
        self.base_url = f'http://{host}:{port}'
        self.logger = logger

    def check_port_available(self):
        """Vérifie si le port est disponible"""
        self.logger.info(f"Vérification de la disponibilité du port {self.port}")
        for conn in psutil.net_connections():
            if conn.laddr.port == self.port:
                self.logger.warning(f"Port {self.port} déjà utilisé par le processus {conn.pid}")
                return False
        return True

    def kill_existing_server(self):
        """Tue les processus Python existants"""
        self.logger.info("Arrêt des serveurs existants")
        try:
            subprocess.run(['ssh', '-o', 'StrictHostKeyChecking=no', 'trn@192.168.0.181', 'pkill -f "python src/web_app.py"'], check=False)
            time.sleep(2)  # Attendre que les processus soient tués
            self.logger.info("Serveurs existants arrêtés avec succès")
        except Exception as e:
            self.logger.warning(f"Erreur lors de l'arrêt des serveurs: {e}")

    def start_server(self):
        """Démarre le serveur Flask"""
        self.logger.info("Démarrage du serveur Flask")
        try:
            # Démarrer le serveur en arrière-plan
            subprocess.Popen([
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                'trn@192.168.0.181',
                'cd /home/trn/citrus && source venv/bin/activate && PYTHONPATH=/home/trn/citrus/src python src/web_app.py'
            ])
            
            # Attendre que le serveur soit prêt
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    time.sleep(2)
                    response = requests.get(f"{self.base_url}/")
                    if response.status_code == 200:
                        self.logger.info("Serveur Flask démarré avec succès")
                        return True
                except requests.exceptions.RequestException:
                    if attempt == max_attempts - 1:
                        self.logger.error("Le serveur n'a pas démarré après plusieurs tentatives")
                        return False
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur: {e}")
            return False

    def test_endpoint(self, endpoint, method='GET', expected_status=200):
        """Teste un endpoint spécifique"""
        url = f"{self.base_url}{endpoint}"
        self.logger.info(f"Test de l'endpoint {url}")
        try:
            response = requests.request(method, url)
            if response.status_code == expected_status:
                self.logger.info(f"Test réussi pour {url}")
                return True
            else:
                self.logger.error(f"Erreur {response.status_code} pour {url}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur de connexion pour {url}: {e}")
            return False

    def check_static_files(self):
        """Vérifie l'accès aux fichiers statiques"""
        static_files = [
            '/static/css/style.css',
            '/static/js/app.js',
            '/static/js/effects/particles.js'
        ]
        
        for file_path in static_files:
            if not self.test_endpoint(file_path):
                return False
        return True

    def run_all_tests(self):
        """Exécute tous les tests"""
        self.logger.info("Démarrage des tests du serveur Citrus")

        # Arrêt des serveurs existants
        self.kill_existing_server()

        # Vérification du port
        if not self.check_port_available():
            self.logger.error(f"Le port {self.port} n'est pas disponible")
            return False

        # Démarrage du serveur
        if not self.start_server():
            return False

        # Test des endpoints principaux
        endpoints = {
            '/': 'GET',
            '/login': 'GET',
            '/logout': 'GET',
            '/api/download': 'POST'
        }

        for endpoint, method in endpoints.items():
            if not self.test_endpoint(endpoint, method):
                return False

        # Test des fichiers statiques
        if not self.check_static_files():
            self.logger.error("Erreur lors du test des fichiers statiques")
            return False

        self.logger.info("Tous les tests ont réussi!")
        return True

if __name__ == '__main__':
    tester = CitrusServerTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
