#!/bin/bash

# ============================
#   🍊 CITRUS RPI MANAGER 🍊
# ============================
#  Gestion complète du Citrus Music Server sur Raspberry Pi
#  Style console premium, couleurs, logs, sécurité et confort !
# ============================

# --- Couleurs et styles ---
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
MAGENTA='\033[1;35m'
WHITE='\033[1;37m'
BOLD='\033[1m'
RESET='\033[0m'

CITRUS_ASCII='\
${YELLOW}\
 ██████╗██╗████████╗██████╗ ██╗   ██╗███████╗\
██╔════╝██║╚══██╔══╝██╔══██╗██║   ██║██╔════╝\
██║     ██║   ██║   ██████╔╝██║   ██║███████╗\
██║     ██║   ██║   ██╔══██╗██║   ██║╚════██║\
╚██████╗██║   ██║   ██║  ██║╚██████╔╝███████║\
 ╚═════╝╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝\
${RESET}\
'

# --- Variables ---
CITRUS_DIR="$(dirname "$(realpath "$0")")/.."
VENV="$CITRUS_DIR/venv"
PYTHON="$VENV/bin/python3"
LOGFILE="$CITRUS_DIR/citrus.log"
BACKUP_DIR="$CITRUS_DIR/backups"

# --- Fonctions utilitaires ---
print_header() {
    clear
    echo -e "$CITRUS_ASCII"
    echo -e "${CYAN}==== Gestionnaire Citrus pour Raspberry Pi ====${RESET}"
}

separator() {
    echo -e "${MAGENTA}----------------------------------------------${RESET}"
}

press_enter() {
    echo -e "\n${YELLOW}Appuie sur Entrée pour continuer...${RESET}"
    read
}

# --- Installation complète ---
install_citrus() {
    print_header
    echo -e "${GREEN}Installation complète de Citrus...${RESET}"
    separator
    sudo apt update && sudo apt install -y python3-pip python3-venv ffmpeg git
    if [ ! -d "$VENV" ]; then
        python3 -m venv "$VENV"
    fi
    source "$VENV/bin/activate"
    pip install --upgrade pip
    pip install -r "$CITRUS_DIR/requirements.txt"
    echo -e "${GREEN}Installation terminée !${RESET}"
    press_enter
}

# --- Lancement du serveur ---
start_citrus() {
    print_header
    echo -e "${GREEN}Démarrage du Citrus Music Server...${RESET}"
    separator
    source "$VENV/bin/activate"
    nohup $PYTHON "$CITRUS_DIR/src/web_app.py" > "$LOGFILE" 2>&1 &
    echo $! > "$CITRUS_DIR/citrus.pid"
    echo -e "${GREEN}Citrus est lancé !${RESET}"
    echo -e "${CYAN}Logs : $LOGFILE${RESET}"
    press_enter
}

# --- Arrêt du serveur ---
stop_citrus() {
    print_header
    echo -e "${RED}Arrêt du Citrus Music Server...${RESET}"
    separator
    if [ -f "$CITRUS_DIR/citrus.pid" ]; then
        kill $(cat "$CITRUS_DIR/citrus.pid") && rm "$CITRUS_DIR/citrus.pid"
        echo -e "${RED}Citrus arrêté.${RESET}"
    else
        echo -e "${YELLOW}Aucun serveur Citrus en cours.${RESET}"
    fi
    press_enter
}

# --- Mise à jour du projet ---
update_citrus() {
    print_header
    echo -e "${BLUE}Mise à jour du projet Citrus...${RESET}"
    separator
    git -C "$CITRUS_DIR" pull
    source "$VENV/bin/activate"
    pip install -r "$CITRUS_DIR/requirements.txt"
    echo -e "${GREEN}Mise à jour terminée !${RESET}"
    press_enter
}

# --- Sauvegarde (backup) ---
backup_citrus() {
    print_header
    separator
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/citrus_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar czf "$BACKUP_FILE" -C "$CITRUS_DIR" src static db
    echo -e "${GREEN}Backup créé : $BACKUP_FILE${RESET}"
    press_enter
}

# --- Affichage des logs ---
show_logs() {
    print_header
    echo -e "${CYAN}Affichage des logs Citrus (Ctrl+C pour quitter)${RESET}"
    separator
    tail -f "$LOGFILE"
}

# --- Menu principal ---
main_menu() {
    while true; do
        print_header
        echo -e "${BOLD}${WHITE}Que veux-tu faire ?${RESET}"
        separator
        echo -e "${GREEN}1.${RESET} Installer Citrus (dépendances, venv, pip)"
        echo -e "${GREEN}2.${RESET} Lancer le serveur Citrus"
        echo -e "${GREEN}3.${RESET} Arrêter le serveur Citrus"
        echo -e "${GREEN}4.${RESET} Mettre à jour Citrus (git pull + pip)"
        echo -e "${GREEN}5.${RESET} Sauvegarder (backup)"
        echo -e "${GREEN}6.${RESET} Afficher les logs"
        echo -e "${GREEN}0.${RESET} Quitter"
        separator
        read -p "${CYAN}Ton choix : ${RESET}" choice
        case $choice in
            1) install_citrus ;;
            2) start_citrus ;;
            3) stop_citrus ;;
            4) update_citrus ;;
            5) backup_citrus ;;
            6) show_logs ;;
            0) echo -e "${YELLOW}À bientôt sur Citrus !${RESET}"; exit 0 ;;
            *) echo -e "${RED}Choix invalide.${RESET}"; sleep 1 ;;
        esac
    done
}

# --- Lancement du menu ---
main_menu
