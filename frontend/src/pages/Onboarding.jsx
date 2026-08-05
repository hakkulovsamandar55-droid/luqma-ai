import { useState } from 'react'
import { ActivityIcon, CheckIcon, RulerIcon, TargetIcon, UserIcon } from '../components/Icons'
import { api } from '../lib/api'
import { haptic, showAlert } from '../lib/telegram'
import './Onboarding.css'

/** Yangi foydalanuvchi uchun profil to'ldirish oqimi (4 qadam). */
const QADAMLAR = [
  {
    key: 'jins',
    Icon: UserIcon,
    title: 'Jinsingiz',
    sub: 'Kaloriya formulasi shunga bog\'liq',
    type: 'choice',
    options: [
      { value: 'erkak', label: 'Erkak' },
      { value: 'ayol', label: 'Ayol' },
    ],
  },
  {
    key: 'olchamlar',
    Icon: RulerIcon,
    title: 'Yosh, bo\'y va vazn',
    sub: 'Aniq hisob uchun kerak',
    type: 'olchamlar',
  },
  {
    key: 'faollik_darajasi',
    Icon: ActivityIcon,
    title: 'Faollik darajangiz',
    sub: 'Kunlik harakat miqdori',
    type: 'choice',
    options: [
      { value: 'sedentary', label: 'Harakatsiz', hint: 'Ofis ishi' },
      { value: 'light', label: 'Yengil', hint: 'Haftada 1-3 kun' },
      { value: 'moderate', label: "O'rtacha", hint: 'Haftada 3-5 kun' },
      { value: 'high', label: 'Yuqori', hint: 'Haftada 6-7 kun' },
      { value: 'athlete', label: 'Juda yuqori', hint: 'Kuniga 2 mashg\'ulot' },
    ],
  },
  {
    key: 'maqsad_turi',
    Icon: TargetIcon,
    title: 'Maqsadingiz',
    sub: 'Nimaga erishmoqchisiz?',
    type: 'choice',
    options: [
      { value: 'yoqotish', label: "Vazn yo'qotish" },
      { value: 'saqlash', label: 'Vaznni saqlash' },
      { value: 'oshirish', label: 'Vazn oshirish' },
    ],
  },
]

export default function Onboarding({ user, onDone }) {
  const [qadam, setQadam] = useState(0)
  const [malumot, setMalumot] = useState({
    jins: user.jins || '',
    yosh: user.yosh || '',
    boy_sm: user.boy_sm || '',
    joriy_vazn_kg: user.joriy_vazn_kg || '',
    istalgan_vazn_kg: user.istalgan_vazn_kg || '',
    faollik_darajasi: user.faollik_darajasi || 'light',
    maqsad_turi: user.maqsad_turi || 'saqlash',
  })
  const [saqlanmoqda, setSaqlanmoqda] = useState(false)

  const joriy = QADAMLAR[qadam]
  const oxirgi = qadam === QADAMLAR.length - 1

  const olchamlarTayyor =
    Number(malumot.yosh) >= 5 &&
    Number(malumot.boy_sm) >= 80 &&
    Number(malumot.joriy_vazn_kg) >= 20

  const davomEtishMumkin =
    joriy.type === 'olchamlar' ? olchamlarTayyor : Boolean(malumot[joriy.key])

  async function keyingi() {
    if (!davomEtishMumkin) return
    haptic('light')

    if (!oxirgi) {
      setQadam((q) => q + 1)
      return
    }

    setSaqlanmoqda(true)
    try {
      const yangilangan = await api.updateUser({
        jins: malumot.jins,
        yosh: Number(malumot.yosh),
        boy_sm: Number(malumot.boy_sm),
        joriy_vazn_kg: Number(malumot.joriy_vazn_kg),
        istalgan_vazn_kg: malumot.istalgan_vazn_kg
          ? Number(malumot.istalgan_vazn_kg)
          : null,
        faollik_darajasi: malumot.faollik_darajasi,
        maqsad_turi: malumot.maqsad_turi,
      })
      haptic('success')
      onDone(yangilangan)
    } catch (e) {
      haptic('error')
      showAlert(e.message)
    } finally {
      setSaqlanmoqda(false)
    }
  }

  return (
    <div className="onb">
      <div className="onb-progress">
        {QADAMLAR.map((_, i) => (
          <span key={i} className={i <= qadam ? 'is-done' : ''} />
        ))}
      </div>

      <div className="onb-body fade-up" key={qadam}>
        <div className="onb-icon">
          <joriy.Icon size={26} />
        </div>
        <h1 className="onb-title">{joriy.title}</h1>
        <p className="onb-sub">{joriy.sub}</p>

        {joriy.type === 'choice' && (
          <div className="onb-choices">
            {joriy.options.map((opt) => (
              <button
                key={opt.value}
                className={`onb-choice ${malumot[joriy.key] === opt.value ? 'is-on' : ''}`}
                onClick={() => {
                  haptic('select')
                  setMalumot((m) => ({ ...m, [joriy.key]: opt.value }))
                }}
              >
                <span>
                  <b>{opt.label}</b>
                  {opt.hint && <small>{opt.hint}</small>}
                </span>
                {malumot[joriy.key] === opt.value && <CheckIcon size={18} />}
              </button>
            ))}
          </div>
        )}

        {joriy.type === 'olchamlar' && (
          <div className="onb-fields">
            {[
              { key: 'yosh', label: 'Yosh', unit: '', ph: '28' },
              { key: 'boy_sm', label: "Bo'y", unit: 'sm', ph: '175' },
              { key: 'joriy_vazn_kg', label: 'Joriy vazn', unit: 'kg', ph: '72' },
              { key: 'istalgan_vazn_kg', label: 'Istalgan vazn', unit: 'kg', ph: '68' },
            ].map((f) => (
              <label className="onb-field" key={f.key}>
                <span>{f.label}</span>
                <span className="onb-field-input">
                  <input
                    type="number"
                    inputMode="decimal"
                    placeholder={f.ph}
                    value={malumot[f.key]}
                    onChange={(e) =>
                      setMalumot((m) => ({ ...m, [f.key]: e.target.value }))
                    }
                  />
                  {f.unit && <i>{f.unit}</i>}
                </span>
              </label>
            ))}
          </div>
        )}
      </div>

      <div className="onb-foot">
        <button
          className="btn btn-primary"
          onClick={keyingi}
          disabled={!davomEtishMumkin || saqlanmoqda}
        >
          {saqlanmoqda ? 'Saqlanmoqda...' : oxirgi ? 'Boshlash' : 'Davom etish'}
        </button>
        {qadam > 0 && (
          <button className="onb-back" onClick={() => setQadam((q) => q - 1)}>
            Orqaga
          </button>
        )}
      </div>
    </div>
  )
}
