#!/bin/bash

# Arrêter en cas d'erreur
set -e

echo "Installation de Citrus Music Server..."

# Vérifier si on est sur Raspberry Pi
if [ ! -f /etc/rpi-issue ]; then
    echo "Ce script doit être exécuté sur un Raspberry Pi"
    exit 1
fi

# Vérifier l'espace disque
FREE_SPACE=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
if (( $(echo "$FREE_SPACE < 2" | bc -l) )); then
    echo "Il faut au moins 2GB d'espace libre"
    exit 1
fi

# Mettre à jour le système
echo "Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

# Installer les dépendances système essentielles
echo "Installation des dépendances système..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    git \
    portaudio19-dev \
    libatlas-base-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff5 \
    libpulse0 \
    libavcodec-extra \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev

# Optimiser les paramètres système
echo "Configuration des paramètres système..."

# Augmenter la limite de fichiers ouverts
sudo bash -c 'cat > /etc/security/limits.d/citrus.conf << EOL
*         soft    nofile          65535
*         hard    nofile          65535
EOL'

# Optimiser la swap
echo "Configuration de la swap..."
SWAP_SIZE=2048
if [ ! -f /swapfile ]; then
    sudo fallocate -l ${SWAP_SIZE}M /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# Créer l'environnement virtuel
echo "Configuration de l'environnement Python..."
python3 -m venv venv
source venv/bin/activate

# Mettre à jour pip
pip install --upgrade pip setuptools wheel

# Installer les dépendances Python
echo "Installation des dépendances Python..."
pip install -r requirements.txt

# Créer les dossiers nécessaires
echo "Création des dossiers..."
mkdir -p src/static/{uploads,music,playlists,cache}
chmod 755 src/static/{uploads,music,playlists,cache}

# Configurer le service systemd avec des limites de ressources
echo "Configuration du service systemd..."
sudo bash -c 'cat > /etc/systemd/system/citrus.service << EOL
[Unit]
Description=Citrus Music Server
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/citrus
Environment="PATH=/home/pi/citrus/venv/bin"
ExecStart=/home/pi/citrus/venv/bin/python src/web_app.py
Restart=always
RestartSec=3

# Limites de ressources
CPUQuota=85%
MemoryLimit=800M
TasksMax=200
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOL'

# Recharger systemd
sudo systemctl daemon-reload
sudo systemctl enable citrus

# Configurer le logging
echo "Configuration du logging..."
sudo mkdir -p /var/log/citrus
sudo chown pi:pi /var/log/citrus

# Configurer la rotation des logs
sudo bash -c 'cat > /etc/logrotate.d/citrus << EOL
/var/log/citrus/*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
EOL'

# Démarrer le service
echo "Démarrage du service..."
sudo systemctl start citrus

# Vérifier le statut
echo "Vérification du statut..."
sleep 5
systemctl status citrus

echo "\nInstallation terminée !"
echo "Le serveur est accessible sur http://$(hostname -I | cut -d' ' -f1):5000"
echo "Les logs sont disponibles dans /var/log/citrus/"
