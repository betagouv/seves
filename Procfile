web: bash bin/start.sh
postdeploy: bash bin/post_deploy.sh
worker: CLAMD_DISABLE_DAEMON=False celery -A seves worker
