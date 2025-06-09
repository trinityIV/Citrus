#!/bin/bash
# =============================================
#  🍊 Citrus - Script de Déploiement Raspberry Pi
# =============================================
# Ce script synchronise tout le projet Citrus sur un Raspberry Pi distant,
# puis exécute le script manager pour installation/lancement.
# Usage : ./deploy_to_rpi.sh <user>@<ip> [chemin_cible]
# =============================================

set -e

# Couleurs
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
RESET='\033[0m'

if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage : $0 <user>@<ip> [chemin_cible]${RESET}"
    exit 1
fi

TARGET_USER_HOST="$1"
TARGET_PATH="${2:-/home/$(echo $1 | cut -d@ -f1)/citrus}"

echo -e "${CYAN}Synchronisation du projet Citrus vers $TARGET_USER_HOST:$TARGET_PATH ...${RESET}"
rsync -av --delete --exclude 'venv/' --exclude '*.pyc' --exclude '__pycache__/' ./ "$TARGET_USER_HOST:$TARGET_PATH/"

echo -e "${GREEN}Transfert terminé !${RESET}"

# Optionnel : demander à lancer le manager à distance
read -p "${YELLOW}Lancer le gestionnaire Citrus sur le Pi distant maintenant ? [o/N] ${RESET}" REP
if [[ "$REP" =~ ^[OoYy]$ ]]; then
    ssh "$TARGET_USER_HOST" "cd $TARGET_PATH/scripts && bash citrus_rpi_manager.sh"
else
    echo -e "${CYAN}Déploiement terminé. Connecte-toi sur le Pi et lance : bash $TARGET_PATH/scripts/citrus_rpi_manager.sh${RESET}"
fi
