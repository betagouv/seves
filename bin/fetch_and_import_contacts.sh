#!/bin/bash

# Ce script récupère et déchiffre les fichiers (export contacts agricoll et clé symétrique) les plus récents depuis le SFTP client
# puis importe les contacts

set -e # exit if any command has a non-zero exit status

bin/fetch_contacts_agricoll_and_key.sh

python manage.py import_contacts agricoll_clear.csv
rm -f agricoll_clear.csv
