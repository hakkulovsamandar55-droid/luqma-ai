"""Mahalliy ovqat bazasi — boshlang'ich ma'lumot.

Nima uchun kerak: har "osh" uchun AI chaqirish pul turadi, sekin ishlaydi
va internet talab qiladi. Ko'p ishlatiladigan taomlar bazada tursa,
qidiruv bir zumda javob beradi va AI faqat notanish taomlar uchun
chaqiriladi.

Qiymatlar 100 g yoki bir odatiy porsiya uchun, ochiq oziq-ovqat
ma'lumotnomalaridan olingan o'rtacha ko'rsatkichlar. Ular taxminiy:
uydagi osh bilan choyxonanikining farqi katta bo'lishi mumkin.
"""

from __future__ import annotations

# (nom, kalit so'zlar, ulush, gramm, kcal, protein, yog', uglevod, turkum)
BOSHLANGICH_OVQATLAR: list[tuple] = [
    # --- Asosiy o'zbek taomlari ---
    ("Osh", "palov plov osh", "1 tovoq (300 g)", 300, 640, 18.0, 28.0, 78.0, "asosiy"),
    ("Manti", "manti mantu", "4 dona (280 g)", 280, 560, 24.0, 26.0, 55.0, "asosiy"),
    ("Somsa", "somsa samsa", "1 dona (120 g)", 120, 330, 12.0, 18.0, 30.0, "asosiy"),
    ("Lag'mon", "lagmon lag'mon laghman", "1 kosa (400 g)", 400, 480, 22.0, 18.0, 58.0, "asosiy"),
    ("Sho'rva", "shorva sho'rva shurpa", "1 kosa (400 g)", 400, 320, 18.0, 14.0, 30.0, "asosiy"),
    ("Mastava", "mastava", "1 kosa (400 g)", 400, 350, 16.0, 12.0, 45.0, "asosiy"),
    ("Chuchvara", "chuchvara pelmen", "1 kosa (300 g)", 300, 420, 20.0, 16.0, 48.0, "asosiy"),
    ("Norin", "norin naryn", "1 tovoq (250 g)", 250, 430, 26.0, 18.0, 42.0, "asosiy"),
    ("Dimlama", "dimlama basma", "1 tovoq (350 g)", 350, 400, 22.0, 20.0, 32.0, "asosiy"),
    ("Shashlik", "shashlik kabob kabab", "2 sixcha (200 g)", 200, 480, 34.0, 36.0, 2.0, "asosiy"),
    ("Qozon kabob", "qozon kabob kazan", "1 porsiya (250 g)", 250, 520, 28.0, 34.0, 26.0, "asosiy"),
    ("Beshbarmoq", "beshbarmoq besh barmoq", "1 tovoq (350 g)", 350, 520, 30.0, 24.0, 45.0, "asosiy"),
    ("Xonim", "xonim honim", "1 porsiya (250 g)", 250, 400, 12.0, 16.0, 52.0, "asosiy"),
    ("Qovurdoq", "qovurdoq qovurma", "1 porsiya (250 g)", 250, 520, 26.0, 38.0, 18.0, "asosiy"),
    ("Tuxum barak", "tuxum barak", "4 dona (200 g)", 200, 380, 14.0, 18.0, 40.0, "asosiy"),
    ("Kabob (jaz)", "jaz kabob", "1 porsiya (200 g)", 200, 460, 24.0, 34.0, 12.0, "asosiy"),
    ("Moshxo'rda", "moshxorda mosh xurda", "1 kosa (400 g)", 400, 300, 14.0, 8.0, 44.0, "asosiy"),

    # --- Non va yormalar ---
    ("Non (obi non)", "non obinon patir", "1 bo'lak (80 g)", 80, 210, 7.0, 1.5, 42.0, "non"),
    ("Patir", "patir qatlama", "1 bo'lak (90 g)", 90, 290, 7.0, 10.0, 42.0, "non"),
    ("Guruch (pishirilgan)", "guruch rice", "100 g", 100, 130, 2.7, 0.3, 28.0, "yorma"),
    ("Grechka (pishirilgan)", "grechka grechixa", "100 g", 100, 110, 4.0, 1.0, 20.0, "yorma"),
    ("Makaron (pishirilgan)", "makaron pasta", "100 g", 100, 130, 5.0, 0.9, 25.0, "yorma"),
    ("Suli bo'tqa", "suli ovsyanka gerkules", "1 kosa (250 g)", 250, 170, 6.0, 3.5, 28.0, "yorma"),

    # --- Go'sht ---
    ("Mol go'shti", "mol gosht govyadina", "100 g", 100, 190, 26.0, 9.0, 0.0, "gosht"),
    ("Qo'y go'shti", "qoy gosht baranina", "100 g", 100, 250, 25.0, 17.0, 0.0, "gosht"),
    ("Tovuq (ko'krak)", "tovuq kurica grudka", "100 g", 100, 165, 31.0, 3.6, 0.0, "gosht"),
    ("Tovuq (son)", "tovuq son okorochok", "100 g", 100, 210, 26.0, 11.0, 0.0, "gosht"),
    ("Baliq", "baliq ryba", "100 g", 100, 130, 22.0, 4.5, 0.0, "gosht"),
    ("Kolbasa", "kolbasa sosiska", "100 g", 100, 300, 12.0, 27.0, 3.0, "gosht"),

    # --- Sut mahsulotlari ---
    ("Tuxum", "tuxum yaytso", "1 dona (60 g)", 60, 78, 6.3, 5.3, 0.6, "sut"),
    ("Qatiq", "qatiq kefir", "1 stakan (250 g)", 250, 145, 8.0, 8.0, 11.0, "sut"),
    ("Tvorog", "tvorog suzma", "100 g", 100, 120, 17.0, 5.0, 3.0, "sut"),
    ("Suzma", "suzma", "100 g", 100, 155, 12.0, 10.0, 4.0, "sut"),
    ("Sut", "sut moloko", "1 stakan (250 ml)", 250, 155, 8.0, 8.5, 12.0, "sut"),
    ("Smetana", "smetana qaymoq", "1 osh qoshiq (25 g)", 25, 50, 0.7, 5.0, 0.8, "sut"),
    ("Pishloq", "pishloq sir", "30 g", 30, 110, 7.0, 9.0, 0.6, "sut"),
    ("Sariyog'", "sariyog maslo", "1 choy qoshiq (10 g)", 10, 75, 0.1, 8.2, 0.1, "sut"),

    # --- Sabzavot ---
    ("Kartoshka (qaynatilgan)", "kartoshka kartofel", "100 g", 100, 85, 2.0, 0.1, 19.0, "sabzavot"),
    ("Kartoshka (qovurilgan)", "fri kartoshka qovurilgan", "100 g", 100, 310, 3.4, 15.0, 40.0, "sabzavot"),
    ("Sabzi", "sabzi morkov", "100 g", 100, 41, 0.9, 0.2, 10.0, "sabzavot"),
    ("Pomidor", "pomidor tomat", "1 dona (120 g)", 120, 22, 1.1, 0.2, 4.7, "sabzavot"),
    ("Bodring", "bodring ogurec", "1 dona (100 g)", 100, 15, 0.7, 0.1, 3.6, "sabzavot"),
    ("Piyoz", "piyoz luk", "100 g", 100, 40, 1.1, 0.1, 9.3, "sabzavot"),
    ("Karam", "karam kapusta", "100 g", 100, 25, 1.3, 0.1, 5.8, "sabzavot"),
    ("Achichuk salat", "achichuk salat", "1 porsiya (150 g)", 150, 45, 1.5, 0.3, 9.0, "sabzavot"),

    # --- Meva ---
    ("Olma", "olma yabloko", "1 dona (180 g)", 180, 95, 0.5, 0.3, 25.0, "meva"),
    ("Banan", "banan", "1 dona (120 g)", 120, 105, 1.3, 0.4, 27.0, "meva"),
    ("Uzum", "uzum vinograd", "100 g", 100, 69, 0.7, 0.2, 18.0, "meva"),
    ("Anor", "anor granat", "1 dona (200 g)", 200, 145, 3.0, 2.0, 33.0, "meva"),
    ("Qovun", "qovun dinya", "1 bo'lak (200 g)", 200, 68, 1.2, 0.3, 16.0, "meva"),
    ("Tarvuz", "tarvuz arbuz", "1 bo'lak (300 g)", 300, 90, 1.8, 0.5, 23.0, "meva"),
    ("O'rik", "orik uruk abrikos", "100 g", 100, 48, 1.4, 0.4, 11.0, "meva"),
    ("Xurmo", "xurmo finik", "3 dona (25 g)", 25, 70, 0.5, 0.1, 18.0, "meva"),

    # --- Ichimlik ---
    ("Choy (shakarsiz)", "choy chay", "1 piyola (200 ml)", 200, 2, 0.0, 0.0, 0.3, "ichimlik"),
    ("Kofe (sutli)", "kofe kofe sutli", "1 stakan (200 ml)", 200, 90, 4.0, 4.0, 9.0, "ichimlik"),
    ("Kompot", "kompot", "1 stakan (250 ml)", 250, 110, 0.2, 0.1, 27.0, "ichimlik"),
    ("Gazli ichimlik", "cola fanta gazli", "1 banka (330 ml)", 330, 140, 0.0, 0.0, 35.0, "ichimlik"),
    ("Ayron", "ayron", "1 stakan (250 ml)", 250, 90, 6.0, 4.0, 8.0, "ichimlik"),

    # --- Shirinlik va gazak ---
    ("Shakar", "shakar sahar", "1 choy qoshiq (5 g)", 5, 20, 0.0, 0.0, 5.0, "shirinlik"),
    ("Asal", "asal myod", "1 osh qoshiq (20 g)", 20, 60, 0.1, 0.0, 16.0, "shirinlik"),
    ("Halva", "halva", "50 g", 50, 260, 6.0, 16.0, 24.0, "shirinlik"),
    ("Pechenye", "pechenye biskvit", "3 dona (30 g)", 30, 140, 2.0, 6.0, 20.0, "shirinlik"),
    ("Shokolad", "shokolad", "30 g", 30, 160, 2.0, 9.0, 18.0, "shirinlik"),
    ("Yong'oq", "yongoq greckiy oreh", "30 g", 30, 195, 4.5, 19.0, 4.0, "gazak"),
    ("Bodom", "bodom mindal", "30 g", 30, 175, 6.0, 15.0, 6.0, "gazak"),
    ("Chipsy", "chips chipsy", "1 paket (75 g)", 75, 400, 5.0, 25.0, 40.0, "gazak"),
]


async def bazani_toldir(session) -> int:
    """Baza bo'sh bo'lsa boshlang'ich ovqatlarni qo'shadi.

    Har ishga tushishda tekshiriladi, lekin faqat bo'sh bazaga yozadi —
    shuning uchun admin o'zgartirgan qiymatlar ustidan yozilmaydi.
    """
    from sqlalchemy import func, select

    from models import FoodItem

    bor = await session.scalar(select(func.count(FoodItem.id))) or 0
    if bor:
        return 0

    for nom, kalit, ulush, gramm, kcal, p, y, u, turkum in BOSHLANGICH_OVQATLAR:
        session.add(
            FoodItem(
                nom=nom,
                kalit_sozlar=kalit,
                ulush=ulush,
                ulush_gramm=gramm,
                kaloriya=kcal,
                protein_g=p,
                yog_g=y,
                uglevod_g=u,
                turkum=turkum,
            )
        )

    await session.commit()
    return len(BOSHLANGICH_OVQATLAR)
