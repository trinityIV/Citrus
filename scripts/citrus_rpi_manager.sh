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
CITRUS_DIR="$HOME/citrus"
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
    sudo apt update && sudo apt install -y python3-pip python3-venv ffmpeg git python3-matplotlib python3-numpy
    # Clonage ou mise à jour du dépôt Citrus (toujours dans $HOME/citrus)
    if [ ! -f "$CITRUS_DIR/requirements.txt" ]; then
        echo -e "${CYAN}Clonage du dépôt Citrus dans $CITRUS_DIR...${RESET}"
        rm -rf "$CITRUS_DIR"
        git clone https://github.com/trinityIV/Citrus.git "$CITRUS_DIR"
    else
        echo -e "${CYAN}Mise à jour du dépôt Citrus...${RESET}"
        git -C "$CITRUS_DIR" pull
    fi
    # Création et activation du venv
    if [ ! -d "$VENV" ]; then
        python3 -m venv "$VENV"
    fi
    source "$VENV/bin/activate"
    pip install --upgrade pip
    pip install -r "$CITRUS_DIR/requirements.txt"
    
    # Installation des dépendances pour les outils d'optimisation
    echo -e "${CYAN}Installation des dépendances pour les outils d'optimisation...${RESET}"
    pip install faker matplotlib numpy
    
    # Installation de yt-dlp pour les téléchargements
    echo -e "${CYAN}Installation de yt-dlp...${RESET}"
    pip install yt-dlp
    
    echo -e "${CYAN}Installation de spotDL (Spotify Downloader)...${RESET}"
    pip install spotdl
    if ! "$VENV/bin/spotdl" --version >/dev/null 2>&1; then
        echo -e "${RED}ERREUR : spotDL n'a pas pu être installé correctement dans le venv !${RESET}"
    else
        echo -e "${GREEN}spotDL installé avec succès.${RESET}"
    fi
    
    # Création des dossiers nécessaires
    mkdir -p "$CITRUS_DIR/src/instance"
    mkdir -p "$CITRUS_DIR/src/optimizations/performance_reports"
    
    echo -e "${GREEN}Installation terminée !${RESET}"
    press_enter
}

# --- Vérification de l'état du serveur ---
check_status() {
    print_header
    echo -e "${BLUE}Vérification de l'état de Citrus Music Server...${RESET}"
    separator
    
    if [ -f "$CITRUS_DIR/citrus.pid" ]; then
        PID=$(cat "$CITRUS_DIR/citrus.pid")
        if ps -p $PID > /dev/null; then
            echo -e "${GREEN}✅ Citrus est en cours d'exécution (PID: $PID)${RESET}"
            
            # Vérifier si le serveur répond
            if command -v curl &> /dev/null; then
                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 2>/dev/null)
                if [ "$HTTP_CODE" = "200" ]; then
                    echo -e "${GREEN}✅ Le serveur web répond correctement (HTTP 200)${RESET}"
                else
                    echo -e "${YELLOW}⚠️ Le serveur web ne répond pas correctement (HTTP $HTTP_CODE)${RESET}"
                fi
            fi
            
            # Afficher l'utilisation des ressources
            echo -e "\n${CYAN}Utilisation des ressources :${RESET}"
            ps -p $PID -o %cpu,%mem,cmd | head -n 2
            
            # Vérifier l'espace disque
            echo -e "\n${CYAN}Espace disque :${RESET}"
            df -h "$CITRUS_DIR" | tail -n 1
        else
            echo -e "${RED}❌ Citrus n'est pas en cours d'exécution (PID $PID introuvable)${RESET}"
            echo -e "${YELLOW}Le fichier PID existe mais le processus est mort.${RESET}"
            rm "$CITRUS_DIR/citrus.pid"
        fi
    else
        echo -e "${RED}❌ Citrus n'est pas en cours d'exécution (pas de fichier PID)${RESET}"
    fi
}

# --- Lancement du serveur ---
start_citrus() {
    print_header
    echo -e "${GREEN}Démarrage du Citrus Music Server...${RESET}"
    separator
    source "$VENV/bin/activate"
    nohup $PYTHON "$CITRUS_DIR/src/run.py" > "$LOGFILE" 2>&1 &
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

# --- Exécution des outils d'optimisation ---
run_optimizations() {
    print_header
    echo -e "${MAGENTA}Outils d'optimisation Citrus${RESET}"
    separator
    source "$VENV/bin/activate"
    
    echo -e "${CYAN}Choisissez un outil d'optimisation :${RESET}"
    echo -e "${GREEN}1.${RESET} Générer des données de test (1000 pistes, 50 playlists)"
    echo -e "${GREEN}2.${RESET} Optimiser les index de base de données"
    echo -e "${GREEN}3.${RESET} Exécuter le benchmark de performances"
    echo -e "${GREEN}4.${RESET} Générer un rapport de monitoring"
    echo -e "${GREEN}0.${RESET} Retour au menu principal"
    separator
    
    read -p "${CYAN}Votre choix : ${RESET}" opt_choice
    case $opt_choice in
        1)
            echo -e "${YELLOW}Génération de données de test...${RESET}"
            $PYTHON "$CITRUS_DIR/src/optimizations/generate_test_data.py"
            ;;
        2)
            echo -e "${YELLOW}Optimisation des index de base de données...${RESET}"
            $PYTHON "$CITRUS_DIR/src/optimizations/optimize_indexes.py"
            ;;
        3)
            echo -e "${YELLOW}Exécution du benchmark de performances...${RESET}"
            $PYTHON "$CITRUS_DIR/src/optimizations/benchmark.py"
            ;;
        4)
            echo -e "${YELLOW}Génération du rapport de monitoring...${RESET}"
            $PYTHON "$CITRUS_DIR/src/optimizations/performance_monitor.py"
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}Choix invalide.${RESET}"
            sleep 1
            ;;
    esac
    
    press_enter
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
        echo -e "${GREEN}7.${RESET} Outils d'optimisation"
        echo -e "${GREEN}8.${RESET} Vérifier l'état du serveur"
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
            7) run_optimizations ;;
            8) check_status; press_enter ;;
            0) echo -e "${YELLOW}À bientôt sur Citrus !${RESET}"; exit 0 ;;
            *) echo -e "${RED}Choix invalide.${RESET}"; sleep 1 ;;
        esac
    done
}

# --- Lancement du menu ---
main_menu
