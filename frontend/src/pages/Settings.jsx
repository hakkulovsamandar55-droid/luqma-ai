import { useEffect, useState } from 'react'
import EditModal from '../components/EditModal'
import {
  ActivityIcon,
  CalendarIcon,
  ChevronRight,
  GenderIcon,
  FireIcon,
  PhoneIcon,
  ProteinIcon,
  RulerIcon,
  ScaleIcon,
  SupportIcon,
  TargetIcon,
  UserIcon,
  WaterIcon,
} from '../components/Icons'
import { api } from '../lib/api'
import {
  FAOLLIK_NOMLARI,
  JINS_NOMLARI,
  MAQSAD_NOMLARI,
  raqam,
} from '../lib/format'
import { haptic, showAlert, showConfirm, tg } from '../lib/telegram'
import { TEMA_NOMI, temaniOqi, temaniOzgartir } from '../lib/theme'
import './Settings.css'

const YORDAM_MANZILI = 'https://t.me/luqma_support'

/** Tahrirlanadigan maydonlar ta'rifi. */
const MAYDONLAR = {
  ism: { key: 'ism', label: 'Ism', type: 'text', Icon: UserIcon },
  telefon: {
    key: 'telefon',
    label: 'Telefon',
    type: 'text',
    Icon: PhoneIcon,
    placeholder: '+998 90 123 45 67',
  },
  yosh: { key: 'yosh', label: 'Yosh', type: 'number', unit: 'yosh', min: 5, max: 120, Icon: CalendarIcon },
  jins: {
    key: 'jins',
    label: 'Jins',
    type: 'choice',
    Icon: GenderIcon,
    options: [
      { value: 'erkak', label: 'Erkak' },
      { value: 'ayol', label: 'Ayol' },
    ],
    hint: 'Kaloriya formulasi jinsga bog\'liq (Mifflin-St Jeor).',
  },
  boy_sm: { key: 'boy_sm', label: "Bo'y", type: 'number', unit: 'sm', min: 80, max: 250, Icon: RulerIcon },
  joriy_vazn_kg: {
    key: 'joriy_vazn_kg',
    label: 'Joriy vazn',
    type: 'number',
    unit: 'kg',
    min: 20,
    max: 400,
    Icon: ScaleIcon,
    hint: 'Har o\'zgartirganingizda vazn tarixiga yoziladi.',
  },
  istalgan_vazn_kg: {
    key: 'istalgan_vazn_kg',
    label: 'Istalgan vazn',
    type: 'number',
    unit: 'kg',
    min: 20,
    max: 400,
    Icon: TargetIcon,
  },
  faollik_darajasi: {
    key: 'faollik_darajasi',
    label: 'Faollik darajasi',
    type: 'choice',
    Icon: ActivityIcon,
    options: [
      { value: 'sedentary', label: 'Harakatsiz', hint: 'Ofis ishi, sport yo\'q' },
      { value: 'light', label: 'Yengil', hint: 'Haftada 1-3 kun mashg\'ulot' },
      { value: 'moderate', label: "O'rtacha", hint: 'Haftada 3-5 kun' },
      { value: 'high', label: 'Yuqori', hint: 'Haftada 6-7 kun' },
      { value: 'athlete', label: 'Juda yuqori', hint: 'Kuniga 2 mashg\'ulot' },
    ],
  },
  maqsad_turi: {
    key: 'maqsad_turi',
    label: 'Maqsad',
    type: 'choice',
    Icon: TargetIcon,
    options: [
      { value: 'yoqotish', label: "Vazn yo'qotish", hint: '−20% kaloriya' },
      { value: 'saqlash', label: 'Vaznni saqlash', hint: 'Muvozanat' },
      { value: 'oshirish', label: 'Vazn oshirish', hint: '+15% kaloriya' },
    ],
  },
  kunlik_kaloriya_limit: {
    key: 'kunlik_kaloriya_limit',
    label: "Kunlik me'yor",
    type: 'number',
    unit: 'kcal',
    min: 800,
    max: 10000,
    Icon: FireIcon,
    hint: 'Qo\'lda o\'zgartirsangiz, avtomatik hisoblash o\'chadi.',
  },
  kunlik_protein_limit: {
    key: 'kunlik_protein_limit',
    label: 'Kunlik oqsil',
    type: 'number',
    unit: 'g',
    min: 0,
    max: 1000,
    Icon: ProteinIcon,
  },
  kunlik_suv_limit_ml: {
    key: 'kunlik_suv_limit_ml',
    label: 'Kunlik suv',
    type: 'number',
    unit: 'ml',
    min: 0,
    max: 10000,
    Icon: WaterIcon,
  },
}

/**
 * Sozlama qatori.
 *
 * Ikonka plitasi (kremrang kvadrat) olib tashlandi: u hech qanday
 * ma'lumot qo'shmasdi va har qatorga og'irlik berardi. Ikonka o'zi
 * och rangda qoldi — u yo'naltiradi, e'tibor tortmaydi.
 */
function Row({ field, value, onClick, danger }) {
  const { Icon, label, sub } = field
  return (
    <button className={`row ${danger ? 'is-danger' : ''}`} onClick={onClick}>
      {/* Ikonka bo'lmasa ham joy band qoladi: aks holda ikonkasiz
          qatorlar chapga siljib, ro'yxatning chap qirrasi tishli
          bo'lib ko'rinadi. */}
      <span className="row-icon">{Icon && <Icon size={19} />}</span>
      <span className="row-text">
        <b>{label}</b>
        {sub && <span>{sub}</span>}
      </span>
      {value !== undefined && (
        <span className={`row-value ${value == null ? 'is-empty' : ''}`}>
          {value ?? 'Kiritilmagan'}
        </span>
      )}
      <ChevronRight size={16} className="row-chev" />
    </button>
  )
}

export default function Settings({
  user,
  onUserChange,
  onOpenWeight,
  onOpenPrivacy,
  onOpenAdmin,
  onOpenPremium,
}) {
  // Admin tugmasi faqat adminlarga ko'rinadi. Backend baribir har so'rovda
  // huquqni tekshiradi — bu shunchaki UI, himoya emas.
  const [adminmi, setAdminmi] = useState(false)
  const [tema, setTema] = useState(temaniOqi)
  const [yordamUser, setYordamUser] = useState('')

  useEffect(() => {
    api
      .getPaymentInfo()
      .then((r) => setYordamUser(r?.yordam_username || ''))
      .catch(() => {})
  }, [])

  useEffect(() => {
    api
      .getAdminMe()
      .then((r) => setAdminmi(Boolean(r?.admin)))
      .catch(() => setAdminmi(false))
  }, [])

  const [tahrir, setTahrir] = useState(null)

  async function saqla(key, value) {
    const yangilangan = await api.updateUser({ [key]: value })
    onUserChange(yangilangan)
  }

  async function limitlarniTikla() {
    if (!(await showConfirm('Limitlar profil asosida qayta hisoblansinmi?'))) return
    try {
      onUserChange(await api.resetLimits())
      haptic('success')
    } catch (e) {
      showAlert(e.message)
    }
  }

  const qiymat = {
    ism: user.ism,
    telefon: user.telefon,
    yosh: user.yosh != null ? `${user.yosh}` : null,
    jins: JINS_NOMLARI[user.jins] ?? null,
    boy_sm: user.boy_sm != null ? `${user.boy_sm} sm` : null,
    joriy_vazn_kg: user.joriy_vazn_kg != null ? `${user.joriy_vazn_kg} kg` : null,
    istalgan_vazn_kg: user.istalgan_vazn_kg != null ? `${user.istalgan_vazn_kg} kg` : null,
    faollik_darajasi: FAOLLIK_NOMLARI[user.faollik_darajasi],
    maqsad_turi: MAQSAD_NOMLARI[user.maqsad_turi],
    kunlik_kaloriya_limit: `${raqam(user.kunlik_kaloriya_limit)} kcal`,
    kunlik_protein_limit: `${user.kunlik_protein_limit} g`,
    kunlik_suv_limit_ml: `${raqam(user.kunlik_suv_limit_ml)} ml`,
  }

  const joriyQiymat = tahrir ? user[tahrir.key] : null

  const bosh = (user.ism || '?').trim().charAt(0).toUpperCase()
  const xulosa = [
    user.yosh && `${user.yosh} yosh`,
    user.boy_sm && `${user.boy_sm} sm`,
    user.joriy_vazn_kg && `${user.joriy_vazn_kg} kg`,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <div className="settings">
      {/* Sahifaning "egasi". Ilgari faqat sarlavha bor edi va sahifa
          kimning sozlamasi ekani ko'rinmasdi. */}
      <header className="prof">
        <div className="prof-ava">{bosh}</div>
        <div className="prof-txt">
          <b>{user.ism || 'Ismsiz'}</b>
          <span>{xulosa || "Profilingizni to'ldiring"}</span>
        </div>
        {user.premium_faolmi && <span className="prof-tag">Premium</span>}
      </header>

      {!user.profil_toliq && (
        <div className="warn-card fade-up">
          <b>Profilingiz to'liq emas</b>
          <p>
            Yosh, jins, bo'y va vaznni kiriting — shunda kunlik me'yoringiz
            aniq hisoblanadi.
          </p>
        </div>
      )}

      <h2 className="section-title">Siz haqingizda</h2>
      <div className="group">
        {['ism', 'telefon', 'yosh', 'jins', 'boy_sm', 'joriy_vazn_kg', 'istalgan_vazn_kg'].map(
          (k) => (
            <Row
              key={k}
              field={MAYDONLAR[k]}
              value={qiymat[k]}
              onClick={() => {
                haptic('light')
                setTahrir(MAYDONLAR[k])
              }}
            />
          )
        )}
      </div>

      <h2 className="section-title">Maqsad va me'yor</h2>
      <div className="group">
        {['maqsad_turi', 'faollik_darajasi', 'kunlik_kaloriya_limit', 'kunlik_protein_limit', 'kunlik_suv_limit_ml'].map(
          (k) => (
            <Row
              key={k}
              field={MAYDONLAR[k]}
              value={qiymat[k]}
              onClick={() => {
                haptic('light')
                setTahrir(MAYDONLAR[k])
              }}
            />
          )
        )}
        <Row
          field={{ label: 'Vazn kuzatuvi', sub: "O'zgarishni grafikda ko'ring", Icon: ScaleIcon }}
          onClick={() => {
            haptic('light')
            onOpenWeight?.()
          }}
        />
      </div>

      {user.limit_qolda && (
        <button className="link-btn" onClick={limitlarniTikla}>
          Me'yorni profil asosida qayta hisoblash
        </button>
      )}

      <h2 className="section-title">Ko'rinish</h2>
      <div className="theme-row">
        {['auto', 'dark', 'light'].map((t) => (
          <button
            key={t}
            className={`theme-opt ${tema === t ? 'is-on' : ''}`}
            onClick={() => {
              haptic('light')
              temaniOzgartir(t)
              setTema(t)
            }}
          >
            {TEMA_NOMI[t]}
          </button>
        ))}
      </div>

      <h2 className="section-title">Boshqa</h2>
      <div className="group">
        {/* Manzil admin panelda sozlanadi — kodda qattiq yozilmagan. */}
        <a
          className="row"
          href={
            yordamUser
              ? `https://t.me/${yordamUser.replace('@', '')}`
              : YORDAM_MANZILI
          }
          target="_blank"
          rel="noreferrer"
        >
          <span className="row-icon">
            <SupportIcon size={19} />
          </span>
          <span className="row-text">
            <b>Yordam</b>
            <span>Telegramda adminga yozing</span>
          </span>
          <ChevronRight size={16} className="row-chev" />
        </a>

        <Row
          field={{ label: 'Maxfiylik siyosati', sub: "Qanday ma'lumot saqlaymiz" }}
          onClick={() => {
            haptic('light')
            onOpenPrivacy?.()
          }}
        />

        {adminmi && (
          <Row
            field={{ label: 'Admin panel', sub: 'Statistika, foydalanuvchilar' }}
            onClick={() => {
              haptic('light')
              onOpenAdmin?.()
            }}
          />
        )}

        <Row
          danger
          field={{ label: "Hisobni o'chirish", sub: "Hamma ma'lumot butunlay o'chadi" }}
          onClick={async () => {
            const tasdiq = await showConfirm(
              "Hisobingiz va barcha ma'lumotlaringiz butunlay o'chiriladi. " +
                "Buni ortga qaytarib bo'lmaydi. Davom etasizmi?"
            )
            if (!tasdiq) return
            haptic('warning')
            try {
              await api.deleteUser()
              await showAlert("Hisobingiz o'chirildi.")
              tg?.close?.()
            } catch (e) {
              showAlert(e.message)
            }
          }}
        />
      </div>

      <p className="version">Luqma AI · v1.0.0</p>

      {tahrir && (
        <EditModal
          field={tahrir}
          value={joriyQiymat}
          onSave={saqla}
          onClose={() => setTahrir(null)}
        />
      )}
    </div>
  )
}
