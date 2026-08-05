#!/usr/bin/env bash
# Birinchi marta Let's Encrypt sertifikatini olish.
#
# Muammo: nginx sertifikatsiz ishga tushmaydi, certbot esa ishlaydigan
# nginx'siz domenni tekshira olmaydi. Yechim — avval vaqtinchalik
# self-signed sertifikat qo'yamiz, keyin haqiqiysiga almashtiramiz.
#
# Ishlatish:  ./scripts/init-ssl.sh

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
    echo "XATO: .env fayli topilmadi. '.env.example' dan nusxa oling." >&2
    exit 1
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

: "${DOMAIN:?DOMAIN .env da ko'rsatilmagan}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL .env da ko'rsatilmagan}"

CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"

echo "==> 1/4  Vaqtinchalik self-signed sertifikat yaratilmoqda (${DOMAIN})"
docker compose run --rm --entrypoint sh certbot -c "
    mkdir -p '${CERT_PATH}' &&
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout '${CERT_PATH}/privkey.pem' \
        -out '${CERT_PATH}/fullchain.pem' \
        -subj '/CN=${DOMAIN}'
"

echo "==> 2/4  Proxy ishga tushirilmoqda"
docker compose up -d proxy
sleep 5

echo "==> 3/4  Vaqtinchalik sertifikat o'chirilib, haqiqiysi so'ralmoqda"
docker compose run --rm --entrypoint sh certbot -c "rm -rf '${CERT_PATH}' /etc/letsencrypt/archive/${DOMAIN} /etc/letsencrypt/renewal/${DOMAIN}.conf"
docker compose run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email "${CERTBOT_EMAIL}" \
    --agree-tos --no-eff-email \
    -d "${DOMAIN}"

echo "==> 4/4  Barcha servislar qayta ishga tushirilmoqda"
docker compose up -d
docker compose exec proxy nginx -s reload

echo
echo "TAYYOR ✅  https://${DOMAIN}"
echo "Endi @BotFather da Mini App manzilini shu domenga sozlang."
