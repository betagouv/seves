#!/bin/bash

# Ce script permet de récupérer le fichier de données chiffré le plus récent et la clé symétrique chiffrée la plus récente
# depuis un serveur SFTP, de les déchiffrer et de stocker le fichier de données déchiffré localement.
# Ce script est invoqué par la commande Django fetch_and_import_contacts.py

set -e # exit if any command has a non-zero exit status
set -u # consider unset variables as errors
set -o pipefail # prevents errors in a pipeline from being masked

: "${SFTP_HOST:?Variable SFTP_HOST non définie}"
: "${SFTP_USERNAME:?Variable SFTP_USERNAME non définie}"
: "${SFTP_PASSWORD:?Variable SFTP_PASSWORD non définie}"
: "${SFTP_PRIVATE_KEY:?Variable SFTP_PRIVATE_KEY non définie}"
: "${SFTP_CLEVERCLOUD_KNOWN_HOSTS:?Variable SFTP_CLEVERCLOUD_KNOWN_HOSTS non définie}"

PRIVATE_KEY_FILENAME="private.key"
ENCRYPTED_SYMMETRIC_KEY_FILENAME="symmetric.key.encrypted"
ENCRYPTED_DATA_FILENAME="agricoll.csv.encrypted"
SYMMETRIC_KEY_FILENAME="symmetric.key"
DATA_FILENAME="agricoll.csv"
# Répertoire où sont stockés les fichiers chiffrés sur le serveur SFTP (par défaut, le répertoire racine)
SFTP_PATH="${SFTP_PATH:-.}"
SFTP_PORT="${SFTP_PORT:-22}"
SFTP_OPTIONS="-P ${SFTP_PORT} -o UserKnownHostsFile=clevercloud_known_hosts -o StrictHostKeyChecking=yes"
SFTP_CONNECT="${SFTP_USERNAME}@${SFTP_HOST}"

# Stocke dans un fichier les cles publiques du serveur SFTP
echo "${SFTP_CLEVERCLOUD_KNOWN_HOSTS}" | base64 --decode > clevercloud_known_hosts

# Récupère la clé symétrique chiffrée la plus récente (fichier .key.encrypted)
sshpass -p "${SFTP_PASSWORD}" sftp ${SFTP_OPTIONS} "${SFTP_CONNECT}" <<EOF > sftp_key_output.txt
ls -lt "${SFTP_PATH}"/*.key.encrypted
bye
EOF
REMOTE_ENCRYPTED_SYMMETRIC_KEY_FILEPATH=$(cat sftp_key_output.txt | grep -v "sftp>" | grep ".key.encrypted" | head -1 | awk '{print $NF}')

# Récupère le fichier de données chiffé le plus récent (fichier .csv.encrypted)
sshpass -p "${SFTP_PASSWORD}" sftp ${SFTP_OPTIONS} "${SFTP_CONNECT}" <<EOF > sftp_data_output.txt
ls -lt "${SFTP_PATH}"/*.csv.encrypted
bye
EOF
REMOTE_ENCRYPTED_DATA_FILEPATH=$(cat sftp_data_output.txt | grep -v "sftp>" | grep ".csv.encrypted" | head -1 | awk '{print $NF}')

# Télécharge les deux fichiers chiffrés (clé symétrique et fichier de données)
sshpass -p "${SFTP_PASSWORD}" sftp ${SFTP_OPTIONS} "${SFTP_CONNECT}":"${REMOTE_ENCRYPTED_SYMMETRIC_KEY_FILEPATH}" "${ENCRYPTED_SYMMETRIC_KEY_FILENAME}"
sshpass -p "${SFTP_PASSWORD}" sftp ${SFTP_OPTIONS} "${SFTP_CONNECT}":"${REMOTE_ENCRYPTED_DATA_FILEPATH}" "${ENCRYPTED_DATA_FILENAME}"

# Déchiffre la clé symétrique
echo "${SFTP_PRIVATE_KEY}" | base64 --decode --ignore-garbage | openssl pkeyutl -decrypt -inkey /dev/stdin -in "${ENCRYPTED_SYMMETRIC_KEY_FILENAME}" -out "${SYMMETRIC_KEY_FILENAME}"

# Déchiffre le fichier de données
openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -in "${ENCRYPTED_DATA_FILENAME}" -out "${DATA_FILENAME}" -pass file:"${SYMMETRIC_KEY_FILENAME}"

rm -f clevercloud_known_hosts \
      sftp_key_output.txt \
      sftp_data_output.txt \
      "${ENCRYPTED_SYMMETRIC_KEY_FILENAME}" \
      "${ENCRYPTED_DATA_FILENAME}" \
      "${SYMMETRIC_KEY_FILENAME}"
