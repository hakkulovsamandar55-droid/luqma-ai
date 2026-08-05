# 🚀 Luqma AI — serverga o'rnatish qo'llanmasi

Noldan to ishlaydigan Mini App gacha. Har bir buyruqni ketma-ket bajaring.

---

## 0. Nima kerak

| Kerak | Izoh |
|---|---|
| **VPS** | Ubuntu 22.04/24.04, kamida **2 GB RAM**, 20 GB disk |
| **Domen** | Masalan `luqma.uz` yoki subdomen `app.luqma.uz` |
| **Bot token** | [@BotFather](https://t.me/BotFather) → `/newbot` |
| **OpenAI kalit** | [platform.openai.com](https://platform.openai.com/api-keys) — balansda pul bo'lsin |

> **Nega 2 GB RAM?** Frontend'ni yig'ish (`npm run build`) xotira talab qiladi.
> 1 GB li serverda build "Killed" bo'lib to'xtashi mumkin — bunda 3-qadamdagi
> **swap** bo'limini bajaring.

> ⚠️ **Telegram Mini App faqat HTTPS orqali ishlaydi.** IP manzil yoki HTTP
> bilan ochilmaydi — shuning uchun domen majburiy.

---

## 1. Domenni serverga ulash (DNS)

Domen sotib olgan saytingiz panelida (ahost.uz, namecheap, cloudflare va h.k.)
**A-yozuv** qo'shing:

| Turi | Nomi | Qiymati |
|---|---|---|
| `A` | `@` (yoki `app`) | Serveringiz IP manzili |

Tekshirish (o'z kompyuteringizda):

```bash
ping luqma.uz
# yoki
nslookup luqma.uz
```

Serverning IP manzili chiqishi kerak. DNS tarqalishi **5 daqiqadan 2 soatgacha**
vaqt olishi mumkin — bu qadam tugamaguncha keyingisiga o'tmang, aks holda
sertifikat olinmaydi.

---

## 2. Serverga kirish

```bash
ssh root@SERVER_IP
```

### Alohida foydalanuvchi yaratish (tavsiya etiladi)

`root` bilan doimiy ishlash xavfli. Alohida foydalanuvchi ochamiz:

```bash
adduser luqma
usermod -aG sudo luqma

# SSH kalitlarni ko'chirib beramiz
rsync --archive --chown=luqma:luqma ~/.ssh /home/luqma

# Endi shu foydalanuvchi bilan kiring
exit
ssh luqma@SERVER_IP
```

---

## 3. Serverni tayyorlash

### Tizimni yangilash

```bash
sudo apt update && sudo apt upgrade -y
```

### Docker o'rnatish

```bash
# Eski versiyalarni olib tashlaymiz
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null

# Rasmiy Docker repozitoriysini qo'shamiz
sudo apt install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# `sudo`siz ishlatish uchun
sudo usermod -aG docker $USER
newgrp docker

# Tekshirish
docker --version && docker compose version
```

### Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

> `OpenSSH` ni ochishni **unutmang** — aks holda serverdan chiqib ketasiz va
> qayta kira olmaysiz.

### Swap (faqat RAM 2 GB dan kam bo'lsa)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

---

## 4. Loyihani yuklab olish

```bash
cd ~
git clone https://github.com/hakkulovsamandar55-droid/luqma-ai.git
cd luqma-ai
```

> Repozitoriy **private** bo'lsa, GitHub'da Personal Access Token yarating
> (Settings → Developer settings → Tokens) va shunday klon qiling:
> `git clone https://TOKEN@github.com/hakkulovsamandar55-droid/luqma-ai.git`

---

## 5. `.env` faylini to'ldirish

```bash
cp .env.example .env
nano .env
```

Quyidagilarni **o'zingiznikiga almashtiring**:

```ini
# Telegram
BOT_TOKEN=8123456789:AAH...siz_olgan_token
WEBAPP_URL=https://luqma.uz          # ← o'z domeningiz, oxirida / QO'YMANG

# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Deploy
DOMAIN=luqma.uz                       # ← https:// SIZ, faqat domen
CERTBOT_EMAIL=sizning@email.uz        # sertifikat tugashi haqida ogohlantirish keladi

# ⚠️ ENG MUHIMI — production'da ALBATTA false
DEV_MODE=false
```

Saqlash: `Ctrl+O` → `Enter` → `Ctrl+X`

### ⚠️ `DEV_MODE` haqida ogohlantirish

`DEV_MODE=true` bo'lsa Telegram `initData` **tekshirilmaydi** — ya'ni
istalgan odam API'ga so'rov yuborib, boshqa foydalanuvchilar nomidan
ma'lumot yozishi mumkin. Productionda **har doim `false`** bo'lsin.

Tekshirish:

```bash
grep DEV_MODE .env      # DEV_MODE=false chiqishi kerak
```

---

## 6. Ishga tushirish

```bash
# Konfiguratsiya to'g'riligini tekshiramiz
docker compose config > /dev/null && echo "config OK"

# Image'larni yig'amiz (birinchi marta 3-7 daqiqa oladi)
docker compose build

# HTTPS sertifikat olish + barcha servislarni ko'tarish
./scripts/init-ssl.sh
```

`init-ssl.sh` nima qiladi:

1. Vaqtinchalik self-signed sertifikat qo'yadi (nginx sertifikatsiz
   ishga tushmaydi)
2. nginx'ni ko'taradi
3. Let's Encrypt'dan haqiqiy sertifikat oladi
4. Hammasini qayta yuklaydi

Oxirida `TAYYOR ✅ https://luqma.uz` chiqishi kerak.

### Holatni tekshirish

```bash
docker compose ps
```

Barcha servislar `running` bo'lishi kerak:

```
luqma-backend    running
luqma-frontend   running
luqma-proxy      running
luqma-certbot    running
```

### API ishlayaptimi?

```bash
curl https://luqma.uz/api/health
# {"status":"ok","app":"luqma-ai"}
```

Brauzerda `https://luqma.uz` ni oching — Luqma AI ekrani chiqishi kerak
(Telegram'siz "Internet aloqasi yo'q" yoki 401 xatosi normal, chunki
`initData` yo'q).

---

## 7. Telegram bot va Mini App sozlash

[@BotFather](https://t.me/BotFather) ga o'ting:

### a) Mini App yaratish

```
/newapp
→ botingizni tanlang
→ App nomi: Luqma AI
→ Tavsif: AI yordamida kaloriya hisoblash
→ Rasm: 640x360 px (istalgan chiroyli rasm)
→ GIF: /empty
→ Web App URL: https://luqma.uz
→ Qisqa nom: luqma
```

### b) Menyu tugmasini sozlash

```
/setmenubutton
→ botingizni tanlang
→ https://luqma.uz
→ Tugma matni: 🥗 Luqma AI
```

### c) Bot tavsifi (ixtiyoriy)

```
/setdescription
→ Ovqatingizni suratga oling — men kaloriya va BJU sini hisoblab beraman!

/setabouttext
→ AI yordamida kaloriya nazorati
```

---

## 8. To'liq sinov

Telegram'da botingizni oching:

| # | Qadam | Kutilgan natija |
|---|---|---|
| 1 | `/start` | Xush kelibsiz xabari + "🥗 Luqma AI ni ochish" tugmasi |
| 2 | Tugmani bosing | Mini App ochiladi, onboarding boshlanadi |
| 3 | Profilni to'ldiring | 4 qadam: jins → o'lchamlar → faollik → maqsad |
| 4 | "Boshlash" | Bosh sahifa, kunlik limit hisoblangan |
| 5 | `+` tugmasi → "Rasmga olish" | Kamera ochiladi |
| 6 | Ovqatni suratga oling | "AI tahlil qilmoqda..." → natija chiqadi |
| 7 | Raqamlarni tekshiring → "Saqlash" | Bosh sahifada ovqat paydo bo'ladi, halqa yangilanadi |
| 8 | `/bugun` (botda) | Bugungi natija matn ko'rinishida |

Agar 6-qadamda xato chiqsa — loglarni ko'ring:

```bash
docker compose logs -f backend
```

---

## 9. Tez-tez uchraydigan muammolar

### `init-ssl.sh` sertifikat ololmadi

```
Timeout during connect / DNS problem
```

**Sabab:** DNS hali tarqalmagan yoki 80-port yopiq.

```bash
# DNS to'g'rimi?
dig +short luqma.uz          # server IP chiqishi kerak

# 80-port ochiqmi?
sudo ufw status
```

DNS to'g'rilangach qayta urinib ko'ring:

```bash
docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
  --email sizning@email.uz --agree-tos --no-eff-email -d luqma.uz
docker compose exec proxy nginx -s reload
```

> Let's Encrypt haftada bitta domen uchun **5 marta** urinish chegarasi bor.
> Ko'p marta xato qilsangiz 1 hafta kutishga to'g'ri keladi — shuning uchun
> avval DNS ni yaxshilab tekshiring.

### Mini App ochilmayapti / oq ekran

- `WEBAPP_URL` va BotFather'dagi URL **bir xil** ekanini tekshiring
- URL `https://` bilan boshlanishi va oxirida `/` **bo'lmasligi** kerak
- Telegram'ni butunlay yopib qayta oching (keshni tozalaydi)

### "Internet aloqasi yo'q" yoki 401

```bash
docker compose logs backend | tail -30
```

- `BOT_TOKEN` `.env` da to'g'ri yozilganmi?
- Token BotFather'dagi **shu bot**niki ekanmi?

### AI tahlili ishlamayapti (502)

```bash
docker compose logs backend | grep -i openai
```

- `OPENAI_API_KEY` to'g'rimi?
- OpenAI hisobingizda **balans** bormi? ([Billing](https://platform.openai.com/settings/organization/billing))

### Build "Killed" bo'lib to'xtadi

RAM yetmayapti — 3-qadamdagi **swap** bo'limini bajaring.

### Portlar band

```bash
sudo lsof -i :80 -i :443
# Agar tizim nginx/apache ishlayotgan bo'lsa:
sudo systemctl stop nginx apache2
sudo systemctl disable nginx apache2
```

---

## 10. Kundalik xizmat ko'rsatish

### Loglar

```bash
docker compose logs -f backend       # backend + bot
docker compose logs -f proxy         # nginx
docker compose logs --tail=100       # hammasi
```

### Qayta ishga tushirish

```bash
docker compose restart backend
docker compose restart              # hammasi
```

### Yangilanishni chiqarish

```bash
cd ~/luqma-ai
git pull
docker compose up -d --build
```

### Bazani zaxiralash (backup)

```bash
mkdir -p ~/backups
docker run --rm \
  -v luqma-ai_luqma-data:/data \
  -v ~/backups:/backup \
  alpine tar czf /backup/luqma-$(date +%F).tar.gz -C /data .

ls -lh ~/backups
```

Har kuni avtomatik zaxira (`crontab -e`):

```cron
0 3 * * * docker run --rm -v luqma-ai_luqma-data:/data -v /home/luqma/backups:/backup alpine tar czf /backup/luqma-$(date +\%F).tar.gz -C /data . && find /home/luqma/backups -name '*.tar.gz' -mtime +14 -delete
```

### Zaxiradan tiklash

```bash
docker compose down
docker run --rm -v luqma-ai_luqma-data:/data -v ~/backups:/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/luqma-2026-08-05.tar.gz -C /data"
docker compose up -d
```

### Sertifikat holati

```bash
docker compose exec certbot certbot certificates
```

Sertifikat avtomatik yangilanadi (certbot konteyneri har 12 soatda tekshiradi),
qo'lda aralashish shart emas.

### Disk joyi

```bash
df -h
docker system df
docker system prune -a       # eski image'larni tozalash
```

---

## 11. Xavfsizlik yakuniy tekshiruvi

Ishga tushirgandan keyin quyidagilarni bir marta tasdiqlang:

```bash
# 1. DEV_MODE o'chiqmi?
grep DEV_MODE ~/luqma-ai/.env          # false bo'lishi shart

# 2. .env git'ga tushmaganmi?
cd ~/luqma-ai && git status --short    # .env ko'rinmasligi kerak

# 3. HTTPS majburiymi?
curl -I http://luqma.uz                # 301 → https

# 4. initData'siz API yopiqmi?
curl -s -o /dev/null -w '%{http_code}\n' https://luqma.uz/api/user/me
# 401 chiqishi kerak. Agar 200 chiqsa — DEV_MODE hali true!
```

To'rtinchi tekshiruv **eng muhimi**: `200` chiqsa, `.env` da `DEV_MODE=false`
qilib `docker compose up -d --force-recreate backend` bajaring.

---

## Qisqacha eslatma (hammasi bir joyda)

```bash
ssh luqma@SERVER_IP
cd ~/luqma-ai

git pull                              # yangilash
docker compose up -d --build          # qayta qurish
docker compose ps                     # holat
docker compose logs -f backend        # loglar
docker compose restart backend        # qayta ishga tushirish
docker compose down                   # to'xtatish
```
