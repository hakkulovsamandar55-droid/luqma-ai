# 🥗 Luqma AI

Telegram Mini App — ovqat rasmini yuboring, AI uni tanib kaloriya va BJU
(oqsil / yog' / uglevod) miqdorini hisoblab beradi. Kunlik limitingizni
maqsadingizga (vazn yo'qotish / saqlash / oshirish) qarab kuzatib boring.

---

## Nima qiladi

| Imkoniyat | Tavsif |
|---|---|
| 📸 **AI rasm tahlili** | Ovqat rasmi → GPT-4o-mini vision → taom nomi, kaloriya, BJU |
| ✍️ **Qo'lda kiritish** | "1 kosa lag'mon va 2 dona non" — matn bo'yicha ham hisoblaydi |
| 🎯 **Shaxsiy limit** | Mifflin-St Jeor formulasi bilan BMR/TDEE va BJU limitlari |
| 📅 **Kunlik kuzatuv** | Kun-tanlagich, progress-ring, qolgan kaloriya va makrolar |
| 💧 **Suv trekeri** | Kun davomida ichilgan stakanlar |
| 📊 **Haftalik trend** | Kaloriya ustunli diagrammasi + limit chizig'i |
| ⚖️ **Vazn tarixi** | Har o'zgarish avtomatik yoziladi |
| ⭐ **Sevimli taomlar** | Tez-tez yeyiladigan taomni bir bosishda qo'shish |
| 🔥 **Streak** | Ketma-ket kuzatilgan kunlar |
| 🔔 **Eslatmalar** | Bot orqali nonushta / tushlik / kechki ovqat eslatmalari |

---

## Texnologiyalar

- **Backend** — Python 3.12, FastAPI, aiogram 3.x, SQLAlchemy 2.0 (async), aiosqlite
- **Frontend** — React 18 + Vite, Telegram Web App SDK (tashqi UI kutubxonasiz)
- **AI** — OpenAI `gpt-4o-mini` vision, structured JSON output
- **Deploy** — Docker Compose + nginx (reverse-proxy, HTTPS/Let's Encrypt)

---

## Loyiha tuzilishi

```
luqma-ai/
├── backend/
│   ├── api.py            # FastAPI — barcha REST endpointlar
│   ├── bot.py            # aiogram bot: /start, Mini App tugmasi, eslatmalar
│   ├── main.py           # API + bot bitta process ichida
│   ├── models.py         # SQLAlchemy modellari
│   ├── db.py             # engine / session / init_db
│   ├── auth.py           # Telegram initData HMAC-SHA256 tekshiruvi
│   ├── nutrition.py      # Mifflin-St Jeor BMR/TDEE va BJU limitlari
│   ├── vision.py         # OpenAI vision integratsiyasi
│   ├── schemas.py        # Pydantic schema'lar
│   ├── config.py         # .env sozlamalari
│   └── tests/            # 33 ta test
├── frontend/
│   ├── src/
│   │   ├── pages/        # Home, AddMeal, Settings, Onboarding
│   │   ├── components/   # ProgressRing, DayStrip, MacroCards, Sheet, ...
│   │   └── lib/          # api.js, telegram.js, format.js
│   └── nginx.conf        # SPA statik serve
├── nginx/nginx.conf      # Tashqi reverse-proxy + HTTPS
├── scripts/init-ssl.sh   # Birinchi Let's Encrypt sertifikati
└── docker-compose.yml
```

---

## Tayyorgarlik

### 1. Telegram bot yaratish

1. [@BotFather](https://t.me/BotFather) → `/newbot` → tokenni oling
2. `/newapp` → botni tanlang → Mini App yarating, URL: `https://sizning-domeningiz.uz`
3. `/setmenubutton` → Mini App manzilini ko'rsating

### 2. OpenAI kaliti

[platform.openai.com](https://platform.openai.com/api-keys) dan API kalit oling.
Bitta rasm tahlili `detail: "low"` rejimida taxminan **$0.0002** turadi.

### 3. `.env` faylini tayyorlang

```bash
cp .env.example .env
nano .env    # BOT_TOKEN, OPENAI_API_KEY, WEBAPP_URL, DOMAIN, CERTBOT_EMAIL
```

> ⚠️ Productionda `DEV_MODE=false` bo'lishi **shart**. `true` bo'lsa
> `initData` tekshirilmaydi va istalgan odam API'ga kira oladi.

---

## Lokal ishga tushirish

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# API + bot birga
python main.py

# yoki alohida:
uvicorn api:app --reload --port 8000
python bot.py
```

API hujjatlari: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Vite `/api` va `/media` so'rovlarini `localhost:8000` ga proxy qiladi.

Brauzerda Telegram SDK bo'lmaganligi uchun `.env` da `DEV_MODE=true` qiling —
shunda `initData`siz ham test qilish mumkin.

### Testlar

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q        # 33 passed
```

---

## Deploy (VPS + Docker Compose)

Talab: domen A-yozuvi serverning IP manziliga ko'rsatilgan bo'lsin, 80 va 443
portlar ochiq bo'lsin.

```bash
git clone <repo> luqma-ai && cd luqma-ai
cp .env.example .env && nano .env      # DOMAIN va CERTBOT_EMAIL ni ham to'ldiring

docker compose build
./scripts/init-ssl.sh                  # birinchi sertifikat + barcha servislar
```

`init-ssl.sh` vaqtinchalik self-signed sertifikat qo'yadi, nginx'ni ko'taradi,
Let's Encrypt'dan haqiqiy sertifikat oladi va qayta yuklaydi. Keyinchalik
`certbot` konteyneri har 12 soatda sertifikatni avtomatik yangilab turadi.

Keyingi deploy'lar:

```bash
git pull && docker compose up -d --build
```

Foydali buyruqlar:

```bash
docker compose logs -f backend      # loglar
docker compose ps                   # holat
docker compose exec proxy nginx -s reload
```

### Servislar

| Servis | Vazifasi |
|---|---|
| `backend` | FastAPI + aiogram bot (8000) |
| `frontend` | nginx, yig'ilgan React statikasi (80) |
| `proxy` | HTTPS tugatish, `/api` → backend, qolgani → frontend |
| `certbot` | Sertifikatni avtomatik yangilash |

Ma'lumotlar `luqma-data` volume ichida (`/data/luqma.db` + `/data/media`).

---

## API

Barcha `/api/*` so'rovlar `Authorization: tma <initData>` sarlavhasini talab
qiladi (backend HMAC-SHA256 bilan tekshiradi).

| Metod | Yo'l | Tavsif |
|---|---|---|
| `POST` | `/api/auth` | initData tekshirish, foydalanuvchi yaratish/topish |
| `GET` | `/api/user/me` | Profil |
| `PUT` | `/api/user/me` | Profilni yangilash + limitlarni qayta hisoblash |
| `POST` | `/api/user/limits/reset` | Qo'lda kiritilgan limitlarni bekor qilish |
| `POST` | `/api/meals/analyze` | Rasm → AI tahlili (saqlanmaydi, preview) |
| `POST` | `/api/meals/analyze-text` | Matn → AI tahlili |
| `POST` | `/api/meals` | Tasdiqlangan ovqatni saqlash |
| `GET` | `/api/meals?date=YYYY-MM-DD` | Kunlik ovqatlar |
| `PUT`/`DELETE` | `/api/meals/{id}` | Tahrirlash / o'chirish |
| `GET` | `/api/stats/summary?date=` | Kunlik progress (qolgan kaloriya/BJU, streak) |
| `GET` | `/api/stats/weekly?date=&kunlar=` | Haftalik trend |
| `GET` | `/api/stats/suggestion` | Qolgan limit asosida AI taom tavsiyasi |
| `POST` | `/api/water` | Suv qo'shish/ayirish |
| `GET`/`POST` | `/api/weight` | Vazn tarixi |
| `GET`/`POST`/`DELETE` | `/api/favorites` | Sevimli taomlar |

---

## Kaloriya qanday hisoblanadi

**Mifflin-St Jeor** formulasi:

```
BMR(erkak) = 10·vazn + 6.25·bo'y − 5·yosh + 5
BMR(ayol)  = 10·vazn + 6.25·bo'y − 5·yosh − 161
TDEE       = BMR × faollik koeffitsienti (1.2 … 1.9)
```

Maqsad bo'yicha tuzatish va makro taqsimoti:

| Maqsad | Kaloriya | Oqsil | Yog' | Uglevod |
|---|---|---|---|---|
| Vazn yo'qotish | −20% | 35% | 30% | 35% |
| Vaznni saqlash | ±0% | 30% | 30% | 40% |
| Vazn oshirish | +15% | 30% | 25% | 45% |

Xavfsizlik uchun quyi chegara: erkaklar 1500 kcal, ayollar 1200 kcal.
Suv maqsadi — `vazn × 33 ml`.

Foydalanuvchi limitni qo'lda o'zgartirsa, avtomatik hisoblash o'chadi
(`limit_qolda`), va uni Sozlamalardagi tugma bilan qayta yoqish mumkin.

---

## Xavfsizlik

- `initData` har bir so'rovda HMAC-SHA256 bilan tekshiriladi (`auth.py`)
- `auth_date` eskirgan bo'lsa rad etiladi (`INITDATA_MAX_AGE`, default 24 soat)
- Foydalanuvchi faqat **o'z** ovqat/vazn yozuvlarini ko'radi va o'chira oladi
- Rasm yuklash: MIME turi va 8MB hajm chegarasi
- AI qaytargan raqamlar xavfsiz chegaralarga qisiladi (`vision._clamp`)
- Telegram Mini App iframe ichida ochilgani uchun `X-Frame-Options` **qo'yilmaydi**

---

## Keyingi bosqichlar

- PostgreSQL'ga o'tish (ORM tayyor — faqat `DATABASE_URL` o'zgaradi)
- Vazn trendi grafigi (ma'lumot allaqachon yig'ilmoqda)
- Limitdan oshganda push-ogohlantirish
- Barkod skaner orqali tayyor mahsulotlar
