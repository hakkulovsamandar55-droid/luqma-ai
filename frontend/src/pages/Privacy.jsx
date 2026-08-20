import './Privacy.css'

/**
 * Maxfiylik siyosati.
 *
 * Ilova yosh, vazn, bo'y kabi shaxsiy ma'lumot yig'adi — bu Telegram Mini App
 * qoidalari bo'yicha ham, mijoz oldida ham hujjatlashtirilishi kerak. Matn
 * ataylab oddiy tilda: yuridik ibora emas, odam tushunadigan jumlalar.
 */
export default function Privacy({ onBack }) {
  return (
    <div className="privacy">
      <header className="privacy-head">
        <button className="privacy-back" onClick={onBack} aria-label="Orqaga">
          <svg viewBox="0 0 24 24" width="21" height="21">
            <path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <h1>Maxfiylik siyosati</h1>
      </header>

      <div className="privacy-body">
        <h2>Qanday ma'lumot saqlaymiz</h2>
        <p>
          Ilova ishlashi uchun quyidagilarni saqlaymiz: Telegram hisobingiz
          raqami va ismingiz, yoshingiz, jinsingiz, bo'yingiz va vazningiz,
          qo'shgan ovqatlaringiz va ularning rasmlari, suv miqdori hamda
          murabbiy bilan yozishmalaringiz.
        </p>

        <h2>Nima uchun kerak</h2>
        <p>
          Yosh, jins, bo'y va vazn kunlik me'yoringizni hisoblash uchun
          ishlatiladi — busiz ilova sizga to'g'ri raqam ayta olmaydi.
          Ovqatlar va rasmlar sizning tarixingizni ko'rsatish uchun saqlanadi.
        </p>

        <h2>Rasmlar</h2>
        <p>
          Yuborgan rasmingiz tahlil qilish uchun OpenAI xizmatiga jo'natiladi.
          Rasm serverimizda 60 kun saqlanadi, keyin avtomatik o'chiriladi.
        </p>

        <h2>Kim ko'ra oladi</h2>
        <p>
          Ma'lumotingizni boshqa foydalanuvchilar ko'ra olmaydi. Biz uni
          sotmaymiz va reklama uchun ishlatmaymiz. Faqat ilova ishlashi uchun
          zarur bo'lgan xizmatlarga (OpenAI, Telegram) uzatiladi.
        </p>

        <h2>O'chirish</h2>
        <p>
          Ma'lumotlaringizni butunlay o'chirishni istasangiz, yordam xizmatiga
          yozing — hisobingiz va unga bog'liq hamma narsa o'chiriladi.
        </p>

        <h2>Muhim eslatma</h2>
        <p>
          Luqma AI shifokor emas va tibbiy maslahat bermaydi. Kaloriya
          hisob-kitobi taxminiy. Kasallik, dori, homiladorlik yoki ovqatlanish
          bilan bog'liq jiddiy savollarda shifokorga murojaat qiling.
        </p>
      </div>
    </div>
  )
}
