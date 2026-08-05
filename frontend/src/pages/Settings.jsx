import { useState } from 'react'
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
import { haptic, showAlert, showConfirm } from '../lib/telegram'
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
    label: 'Kunlik kaloriya limiti',
    type: 'number',
    unit: 'kcal',
    min: 800,
    max: 10000,
    Icon: FireIcon,
    hint: 'Qo\'lda o\'zgartirsangiz, avtomatik hisoblash o\'chadi.',
  },
  kunlik_protein_limit: {
    key: 'kunlik_protein_limit',
    label: 'Kunlik oqsil limiti',
    type: 'number',
    unit: 'g',
    min: 0,
    max: 1000,
    Icon: ProteinIcon,
  },
  kunlik_suv_limit_ml: {
    key: 'kunlik_suv_limit_ml',
    label: 'Kunlik suv maqsadi',
    type: 'number',
    unit: 'ml',
    min: 0,
    max: 10000,
    Icon: WaterIcon,
  },
}

function Row({ field, value, onClick }) {
  const { Icon, label } = field
  return (
    <button className="row" onClick={onClick}>
      <span className="row-icon">
        <Icon size={18} />
      </span>
      <span className="row-label">{label}</span>
      <span className={`row-value ${value == null ? 'is-empty' : ''}`}>
        {value ?? 'Kiritilmagan'}
      </span>
      <ChevronRight size={17} className="row-chev" />
    </button>
  )
}

export default function Settings({ user, onUserChange }) {
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

  return (
    <div className="settings">
      <h1 className="page-title">Sozlamalar</h1>

      {!user.profil_toliq && (
        <div className="warn-card fade-up">
          <b>Profilingiz to'liq emas</b>
          <p>
            Yosh, jins, bo'y va vaznni kiriting — shunda kunlik kaloriya limitingiz
            aniq hisoblanadi.
          </p>
        </div>
      )}

      <h2 className="section-title">Hisob</h2>
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

      <h2 className="section-title">Maqsadlar va kuzatuv</h2>
      <div className="group">
        {[
          'maqsad_turi',
          'faollik_darajasi',
          'kunlik_kaloriya_limit',
          'kunlik_protein_limit',
          'kunlik_suv_limit_ml',
        ].map((k) => (
          <Row
            key={k}
            field={MAYDONLAR[k]}
            value={qiymat[k]}
            onClick={() => {
              haptic('light')
              setTahrir(MAYDONLAR[k])
            }}
          />
        ))}
      </div>

      {user.limit_qolda && (
        <button className="reset-btn" onClick={limitlarniTikla}>
          Limitlarni formula bo'yicha qayta hisoblash
        </button>
      )}

      <h2 className="section-title">Yordam xizmati</h2>
      <div className="group">
        <a className="row" href={YORDAM_MANZILI} target="_blank" rel="noreferrer">
          <span className="row-icon">
            <SupportIcon size={18} />
          </span>
          <span className="row-label">Qo'llab-quvvatlash</span>
          <span className="row-value">Telegram</span>
          <ChevronRight size={17} className="row-chev" />
        </a>
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
