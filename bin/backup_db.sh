#!/usr/bin/env bash
: "${BACKUP_API_TOKEN:?Variable BACKUP_API_TOKEN non définie}"
: "${BACKUP_SOURCE_APP:?Variable BACKUP_SOURCE_APP non définie}"
: "${BACKUP_BUCKET_NAME:?Variable BACKUP_BUCKET_NAME non définie}"
: "${BACKUP_S3_ENDPOINT:?Variable BACKUP_S3_ENDPOINT non définie}"
: "${AWS_ACCESS_KEY_ID:?Variable AWS_ACCESS_KEY_ID non définie}"
: "${AWS_SECRET_ACCESS_KEY:?Variable AWS_SECRET_ACCESS_KEY non définie}"

archive_name="backup_$(date +'%Y-%m-%d').tar.gz"
pip install "awscli<1.36.0"
install-scalingo-cli

scalingo login --api-token "${BACKUP_API_TOKEN}"

# Retrieve the addon id:
addon_id="$( scalingo --region osc-secnum-fr1 --app "${BACKUP_SOURCE_APP}" addons \
             | grep "postgresql" \
             | cut -d "|" -f 3 \
             | tr -d " " )"

# Download the latest backup available for the specified addon:
scalingo --region osc-secnum-fr1 --app "${BACKUP_SOURCE_APP}" --addon "${addon_id}" backups-download --output "${archive_name}"

aws --endpoint-url=${BACKUP_S3_ENDPOINT} s3 cp ${archive_name} s3://${BACKUP_BUCKET_NAME}
