# Bosh sahifa — 6 xil dizayn

Klient dizaynni tanlashi uchun tayyorlangan statik maketlar. Hammasida
ma'lumot **bir xil** (1723 kcal qoldi, o'sha makrolar, o'sha 2 ta ovqat) —
shunda farq faqat dizaynda ko'rinadi.

Bular ranglari almashtirilgan bitta dizayn EMAS. Har birida rang tizimi,
tipografika, ikonka tili, tugma arxitekturasi va ekran tuzilishi boshqacha:

| # | Nomi | Rang | Shrift | Asosiy ko'rsatkich | Tugmalar | Navigatsiya |
|---|------|------|--------|--------------------|----------|-------------|
| 1 | Brutalist | Qora + kislotali sariq | Archivo Black + Plex Mono | Konturli qutida ulkan raqam, progress — bloklar | To'rtburchak, radius yo'q, qattiq soya | Pastda 5 ta to'rtburchak katak |
| 2 | Yumshoq | Krem + shalfey + terrakota | Fraunces + Nunito | Yumshoq halqa | To'liq dumaloq, past kontrast | Suzuvchi dumaloq panel |
| 3 | Panel | Qora + firuza | IBM Plex Mono | Raqam + sparkline + jadval | 1px konturli to'rtburchak | Tepada chiziqli tab |
| 4 | Jurnal | Oq qog'oz + qizil | Instrument Serif + Inter | 110px serif raqam | Matn havolasi + bitta qora tugma | Tepada matn havolalari |
| 5 | O'yin | Binafsha-pushti gradient + lime | Fredoka | To'lib boruvchi shisha + XP | Qalin dumaloq, "3D" soya | Pastda pufakchali panel |
| 6 | Tizim | iOS kulrang + ko'k | Inter | Activity halqalari + ro'yxat | Ko'k matn tugma, segment | Standart iOS tab bar |

## Ko'rish

```bash
cd design/home-variants
npm install     # shriftlar (tashqi so'rov yo'q, hammasi paketda)
npm start       # http://localhost:5199/1-brutalist.html
```

Shriftlar o'rnatilmasa ham maket ochiladi — faqat tipografika tizim
shriftiga tushadi, joylashuv va ranglar o'z holicha qoladi.
