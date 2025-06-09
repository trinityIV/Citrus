#!/bin/bash

# Fonction pour les logs colorés
log() {
    local level=$1
    shift
    local msg="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    case "$level" in
        "INFO")  echo -e "\e[34m[INFO ]\e[0m $timestamp - $msg" | tee -a install.log ;;
        "WARN")  echo -e "\e[33m[WARN ]\e[0m $timestamp - $msg" | tee -a install.log ;;
        "ERROR") echo -e "\e[31m[ERROR]\e[0m $timestamp - $msg" | tee -a install.log ;;
        "OK")    echo -e "\e[32m[ OK  ]\e[0m $timestamp - $msg" | tee -a install.log ;;
    esac
}

# Fonction pour afficher la progression
show_progress() {
    local duration=$1
    local step=$2
    local width=50
    local progress=0
    
    while [ $progress -le 100 ]; do
        local num_chars=$(($progress * $width / 100))
        local num_spaces=$((width - num_chars))
        printf "\r[%${num_chars}s%${num_spaces}s] %d%%" "${step}" | tr ' ' '#' | tr '#' ' '
        progress=$((progress + 2))
        sleep $(echo "scale=3; $duration/50" | bc)
    done
    echo
}

# Fonction pour vérifier les prérequis
check_prerequisites() {
    log "INFO" "Vérification des prérequis..."
    
    # Vérifier si on est sur Raspberry Pi
    if [ ! -f /etc/rpi-issue ]; then
        log "ERROR" "Ce script doit être exécuté sur un Raspberry Pi"
        exit 1
    fi
    log "OK" "Système Raspberry Pi détecté"
    
    # Vérifier l'espace disque
    FREE_SPACE=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( $(echo "$FREE_SPACE < 2" | bc -l) )); then
        log "ERROR" "Il faut au moins 2GB d'espace libre"
        exit 1
    fi
    log "OK" "Espace disque suffisant: ${FREE_SPACE}GB disponible"
    
    # Vérifier la connexion Internet
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        log "ERROR" "Pas de connexion Internet"
        exit 1
    fi
    log "OK" "Connexion Internet vérifiée"
}

# ASCII Art
cat << "EOF"

  ██████╗██╗████████╗██████╗ ██╗   ██╗███████╗    ███╗   ███╗██╗   ██╗███████╗██╗ ██████╗
 ██╔════╝██║╚══██╔══╝██╔══██╗██║   ██║██╔════╝    ████╗ ████║██║   ██║██╔════╝██║██╔════╝
 ██║     ██║   ██║   ██████╔╝██║   ██║███████╗    ██╔████╔██║██║   ██║███████╗██║██║     
 ██║     ██║   ██║   ██╔══██╗██║   ██║╚════██║    ██║╚██╔╝██║██║   ██║╚════██║██║██║     
 ╚██████╗██║   ██║   ██║  ██║╚██████╔╝███████║    ██║ ╚═╝ ██║╚██████╔╝███████║██║╚██████╗
  ╚═════╝╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝    ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝ ╚═════╝
                                                                                           
                        ✨ Installateur par 0xvertake$ ✨
                        Version 1.0.0 - Build 2025.06.09

EOF

echo -e "\n╔══════════════════════════════════════════════════════════════════╗"
echo -e "║                     Installation de Citrus Music                        ║"
echo -e "╚══════════════════════════════════════════════════════════════════╝\n"

# Initialiser le fichier de log
echo "=== Début de l'installation $(date) ===" > install.log

# Vérifier les prérequis
check_prerequisites

# Mettre à jour le système
log "INFO" "Mise à jour du système..."
if sudo apt update && sudo apt upgrade -y >> install.log 2>&1; then
    log "OK" "Système mis à jour"
else
    log "ERROR" "Erreur lors de la mise à jour du système"
    exit 1
fi

# Installer les dépendances système
log "INFO" "Installation des dépendances système..."
DEPS=(
    "python3-pip" "python3-venv" "python3-dev" "ffmpeg" "git"
    "portaudio19-dev" "libatlas-base-dev" "libjpeg-dev" "zlib1g-dev"
    "libfreetype6-dev" "liblcms2-dev" "libopenjp2-7" "libtiff5"
    "libpulse0" "libavcodec-extra" "libavformat-dev" "libswscale-dev"
    "libv4l-dev" "libxvidcore-dev" "libx264-dev"
)

for dep in "${DEPS[@]}"; do
    log "INFO" "Installation de $dep..."
    if sudo apt install -y "$dep" >> install.log 2>&1; then
        log "OK" "$dep installé"
        show_progress 0.5 "$dep"
    else
        log "ERROR" "Erreur lors de l'installation de $dep"
        exit 1
    fi
done

# Optimiser le système
log "INFO" "Configuration du système..."

# Limites système
log "INFO" "Configuration des limites système..."
sudo bash -c 'cat > /etc/security/limits.d/citrus.conf << EOL
*         soft    nofile          65535
*         hard    nofile          65535
EOL'
log "OK" "Limites système configurées"

# Configuration de la swap
log "INFO" "Configuration de la swap..."
SWAP_SIZE=2048
if [ ! -f /swapfile ]; then
    sudo fallocate -l ${SWAP_SIZE}M /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile >> install.log 2>&1
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >> install.log 2>&1
    log "OK" "Swap de ${SWAP_SIZE}MB configurée"
fi

# Configuration Python
log "INFO" "Configuration de l'environnement Python..."
python3 -m venv venv >> install.log 2>&1
source venv/bin/activate
pip install --upgrade pip setuptools wheel >> install.log 2>&1
log "OK" "Environnement Python configuré"

# Installation des dépendances Python
log "INFO" "Installation des dépendances Python..."
if pip install -r requirements.txt >> install.log 2>&1; then
    log "OK" "Dépendances Python installées"
else
    log "ERROR" "Erreur lors de l'installation des dépendances Python"
    exit 1
fi

# Création des dossiers
log "INFO" "Création des dossiers..."
mkdir -p src/static/{uploads,music,playlists,cache}
chmod 755 src/static/{uploads,music,playlists,cache}
log "OK" "Dossiers créés"

# Configuration du service
log "INFO" "Configuration du service systemd..."
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

# Configuration des logs
log "INFO" "Configuration du logging..."
sudo mkdir -p /var/log/citrus
sudo chown pi:pi /var/log/citrus

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
log "OK" "Logging configuré"

# Démarrage du service
log "INFO" "Démarrage du service..."
sudo systemctl daemon-reload
sudo systemctl enable citrus >> install.log 2>&1
sudo systemctl start citrus

# Vérification finale
log "INFO" "Vérification du service..."
sleep 5
if systemctl is-active --quiet citrus; then
    log "OK" "Service démarré avec succès"
else
    log "ERROR" "Erreur lors du démarrage du service"
    exit 1
fi

# Résumé final
IP_ADDRESS=$(hostname -I | cut -d' ' -f1)

echo -e "\n╔══════════════════════════════════════════════════════════════════╗"
echo -e "║                    Installation terminée avec succès !                    ║"
echo -e "╚══════════════════════════════════════════════════════════════════╝\n"

log "INFO" "=== Installation terminée ==="
log "INFO" "Interface web disponible sur: http://$IP_ADDRESS:5000"
log "INFO" "Logs disponibles dans: /var/log/citrus/"
log "INFO" "Log d'installation: $(pwd)/install.log"

echo -e "\n✨ Profitez de votre Citrus Music Server ! ✨\n"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
SERVICE_NAME="citrus"
INSTALL_DIR="/opt/citrus"
USER="citrus"
GROUP="citrus"

# Fonction pour afficher la progression
show_progress() {
    echo -e "${BLUE}$1...${NC}"
}

# Fonction pour afficher les erreurs
show_error() {
    echo -e "${RED}Erreur: $1${NC}"
    exit 1
}

# Vérifier les privilèges root
if [ "$EUID" -ne 0 ]; then
    show_error "Ce script doit être exécuté en tant que root"
fi

# 1. Mise à jour du système
show_progress "1. Mise à jour du système"
apt update || show_error "Impossible de mettre à jour apt"
apt upgrade -y || show_error "Impossible de mettre à jour le système"

# 2. Installation des dépendances système
show_progress "2. Installation des dépendances système"
apt install -y python3 python3-pip python3-venv git ffmpeg \
    build-essential cmake \
    python3-pyqt6 python3-pyqt6.qtwebengine python3-pyqt6.qtmultimedia \
    libpulse0 libpulse-dev portaudio19-dev python3-pyaudio \
    ufw || show_error "Impossible d'installer les dépendances système"

# 3. Création de l'utilisateur et du groupe
show_progress "3. Configuration de l'utilisateur"
if ! getent group $GROUP >/dev/null; then
    groupadd $GROUP
fi
if ! getent passwd $USER >/dev/null; then
    useradd -r -g $GROUP -d $INSTALL_DIR $USER
fi

# 4. Création et configuration du répertoire d'installation
show_progress "4. Configuration du répertoire d'installation"
mkdir -p $INSTALL_DIR
chown -R $USER:$GROUP $INSTALL_DIR

# 5. Clonage du dépôt
show_progress "5. Installation de l'application"
cd $INSTALL_DIR
git clone https://github.com/yourusername/citrus.git . || show_error "Impossible de cloner le dépôt"

# 6. Configuration de l'environnement Python
show_progress "6. Configuration de l'environnement Python"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 7. Configuration du service systemd
show_progress "7. Configuration du service systemd"
cat > /etc/systemd/system/$SERVICE_NAME.service << EOL
[Unit]
Description=Citrus Music Server
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR/src
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=$INSTALL_DIR/venv/lib/python3.11/site-packages
ExecStart=$INSTALL_DIR/venv/bin/python web_app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# 8. Configuration du firewall
show_progress "8. Configuration du firewall"
ufw allow ssh
ufw allow 5000/tcp comment 'Citrus Web Interface'
ufw --force enable

# 9. Démarrage du service
show_progress "9. Démarrage du service"
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# 10. Vérification finale
show_progress "10. Vérification de l'installation"
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}Installation terminée avec succès !${NC}"
    echo -e "Accédez à l'interface web : http://$(hostname -I | cut -d' ' -f1):5000"
else
    show_error "Le service n'a pas démarré correctement"
fi
