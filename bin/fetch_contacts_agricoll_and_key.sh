#!/bin/bash

# Ce script permet de récupérer le fichier de données chiffré le plus récent et la clé symétrique chiffrée la plus récente
# depuis un serveur SFTP, de les déchiffrer et de stocker le fichier de données déchiffré localement.
# Ce script est invoqué par la commande Django fetch_and_import_contacts.py

PRIVATE_KEY_FILENAME="private.key"
SYMMETRIC_KEY_FILENAME="symmetric.key"
DATA_FILENAME="agricoll.csv"
# Le premier paramètre est le chemin SFTP, par défaut c'est la racine
SFTP_PATH="${1:-.}"

# Stocke dans un fichier les cles publiques du serveur SFTP
echo $SFTP_CLEVERCLOUD_KNOWN_HOSTS | base64 -d > clevercloud_known_hosts

# Récupère la clé symétrique chiffrée la plus récente (fichier .key.encrypted)
sshpass -p "$SFTP_PASSWORD" sftp -o UserKnownHostsFile=clevercloud_known_hosts -o StrictHostKeyChecking=yes "$SFTP_USERNAME@$SFTP_HOST" <<EOF > sftp_key_output.txt
cd ${SFTP_PATH}
ls -lt *.key.encrypted
bye
EOF
LATEST_ENCRYPTED_KEY_FILENAME=$(cat sftp_key_output.txt | grep -v "sftp>" | grep ".key.encrypted" | head -1 | awk '{print $NF}')

# Récupère le fichier de données chiffé le plus récent (fichier .csv.encrypted)
sshpass -p "$SFTP_PASSWORD" sftp -o UserKnownHostsFile=clevercloud_known_hosts -o StrictHostKeyChecking=yes "$SFTP_USERNAME@$SFTP_HOST" <<EOF > sftp_data_output.txt
cd ${SFTP_PATH}
ls -lt *.csv.encrypted
bye
EOF
LATEST_ENCRYPTED_DATA_FILENAME=$(cat sftp_data_output.txt | grep -v "sftp>" | grep ".csv.encrypted" | head -1 | awk '{print $NF}')

# Télécharge les deux fichiers chiffrés (clé symétrique et fichier de données)
sshpass -p "$SFTP_PASSWORD" scp -o UserKnownHostsFile=clevercloud_known_hosts -o StrictHostKeyChecking=yes "$SFTP_USERNAME@$SFTP_HOST:$SFTP_PATH/$LATEST_ENCRYPTED_KEY_FILENAME" .
sshpass -p "$SFTP_PASSWORD" scp -o UserKnownHostsFile=clevercloud_known_hosts -o StrictHostKeyChecking=yes "$SFTP_USERNAME@$SFTP_HOST:$SFTP_PATH/$LATEST_ENCRYPTED_DATA_FILENAME" .

# Déchiffre la clé symétrique
echo $SFTP_PRIVATE_KEY | base64 -d > $PRIVATE_KEY_FILENAME
chmod 600 $PRIVATE_KEY_FILENAME
openssl pkeyutl -decrypt -inkey $PRIVATE_KEY_FILENAME -in $LATEST_ENCRYPTED_KEY_FILENAME -out $SYMMETRIC_KEY_FILENAME

# Déchiffre le fichier de données
openssl enc -d -aes-256-cbc -a -salt -pbkdf2 -in ${LATEST_ENCRYPTED_DATA_FILENAME} -out $DATA_FILENAME -pass file:$SYMMETRIC_KEY_FILENAME

rm -f clevercloud_known_hosts
rm -f sftp_key_output.txt
rm -f sftp_data_output.txt
rm -f $LATEST_ENCRYPTED_KEY_FILENAME
rm -f $LATEST_ENCRYPTED_DATA_FILENAME
rm -f $PRIVATE_KEY_FILENAME
rm -f $SYMMETRIC_KEY_FILENAME
