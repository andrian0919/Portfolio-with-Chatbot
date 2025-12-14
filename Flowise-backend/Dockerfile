FROM node:18-alpine

ENV PORT=3000 \
    DATABASE_PATH=/var/data/flowise \
    BLOB_STORAGE_PATH=/var/data/flowise/storage \
    LOG_PATH=/var/data/flowise/logs

RUN apk add --no-cache bash \
    && npm install -g flowise \
    && mkdir -p /var/data/flowise/storage /var/data/flowise/logs

EXPOSE 3000

CMD ["sh", "-lc", "flowise start --PORT=${PORT} --DATABASE_PATH=${DATABASE_PATH} --BLOB_STORAGE_PATH=${BLOB_STORAGE_PATH} --LOG_PATH=${LOG_PATH}"]
