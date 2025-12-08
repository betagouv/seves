#!/bin/bash

set -e
set -u
export AWS_REQUEST_CHECKSUM_CALCULATION=WHEN_REQUIRED
export AWS_RESPONSE_CHECKSUM_VALIDATION=WHEN_REQUIRED # Not supported by outscale
pip install "awscli<1.36.0"

: "${BUCKET_SOURCE:?Variable BUCKET_SOURCE non définie}"
: "${AWS_ACCESS_KEY_ID_SOURCE:?Variable AWS_ACCESS_KEY_ID_SOURCE non définie}"
: "${AWS_SECRET_ACCESS_KEY_SOURCE:?Variable AWS_SECRET_ACCESS_KEY_SOURCE non définie}"
: "${AWS_REGION_SOURCE:?Variable AWS_REGION_SOURCE non définie}"
: "${S3_ENDPOINT_SOURCE:?Variable S3_ENDPOINT_SOURCE non définie}"

: "${LOCAL_TEMP_DIR:?Variable LOCAL_TEMP_DIR non définie}"

: "${BUCKET_DESTINATION:?Variable BUCKET_DESTINATION non définie}"
: "${AWS_ACCESS_KEY_ID_DESTINATION:?Variable AWS_ACCESS_KEY_ID_DESTINATION non définie}"
: "${AWS_SECRET_ACCESS_KEY_DESTINATION:?Variable AWS_SECRET_ACCESS_KEY_DESTINATION non définie}"
: "${AWS_REGION_DESTINATION:?Variable AWS_REGION_DESTINATION non définie}"
: "${S3_ENDPOINT_DESTINATION:?Variable S3_ENDPOINT_DESTINATION non définie}"


echo "=== Début de la synchronisation ==="

# Créer le dossier temporaire
mkdir -p $LOCAL_TEMP_DIR

# Étape 1 : Télécharger depuis bucket A
echo "[1/2] Téléchargement depuis $BUCKET_SOURCE..."
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID_SOURCE \
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY_SOURCE \
AWS_DEFAULT_REGION=$AWS_REGION_SOURCE \
aws s3 sync s3://$BUCKET_SOURCE/ $LOCAL_TEMP_DIR/ --endpoint-url $S3_ENDPOINT_SOURCE


## Étape 2 : Upload incrémental vers bucket B
echo "[2/2] Synchronisation vers $BUCKET_DESTINATION..."
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID_DESTINATION \
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY_DESTINATION \
AWS_DEFAULT_REGION=$AWS_REGION_DESTINATION \
aws s3 sync $LOCAL_TEMP_DIR/ s3://$BUCKET_DESTINATION/ --endpoint-url $S3_ENDPOINT_DESTINATION

echo "=== Synchronisation terminée avec succès ! ==="
