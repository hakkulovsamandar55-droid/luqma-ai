import { useEffect, useState } from 'react'
import Sheet from './Sheet'
import { PlateIcon } from './Icons'
import { api } from '../lib/api'
import { vaqtQisqa } from '../lib/format'
import { haptic } from '../lib/telegram'
import './MealSheet.css'

/**
 * Saqlangan ovqatni ko'rish va tahrirlash.
 *
 * Ro'yxatdagi qator ilgari ham bosiladigan tugma edi, lekin uni bosganda
 * hech narsa ochilmasdi — hech kim `onOpen` ni ulamagan. Ya'ni AI xato
 * hisoblasa (bu tez-tez bo'ladi: "1 kosa" turlicha bo'ladi), qiymatni
 * to'g'irlashning yagona yo'li ovqatni o'chirib, qaytadan kiritish edi.
 *
 * Shuning uchun bu oyna to'g'irlashga qulay: har bir raqam alohida
 * maydonda va gramm bo'yicha qayta hisoblash tugmasi bor.
 */
const MAKROLAR = [
  { key: 'protein_g', label: 'Oqsil', unit: 'g' },
  { key: 'yog_g', label: "Yog'", unit: 'g' },
  { key: 'uglevod_g', label: 'Uglevod', unit: 'g' },
]

function son(v) {
  const n = Number(String(v ?? '').replace(',', '.'))
  return Number.isFinite(n) && n >= 0 ? n : null
}

export default function MealSheet({ meal, onClose, onSaved, onDelete }) {
  const [form, setForm] = useState(null)
  const [saqlanmoqda, setSaqlanmoqda] = useState(false)
  const [xato, setXato] = useState(null)

  useEffect(() => {
    if (!meal) return
    setXato(null)
    setForm({
      taom_nomi: meal.taom_nomi ?? '',
      ulush: meal.ulush ?? '',
      kaloriya: String(meal.kaloriya ?? 0),
      protein_g: String(meal.protein_g ?? 0),
      yog_g: String(meal.yog_g ?? 0),
      uglevod_g: String(meal.uglevod_g ?? 0),
    })
  }, [meal])

  if (!meal || !form) return null

  const yangila = (key, qiymat) => setForm((f) => ({ ...f, [key]: qiymat }))

  /* Makrolardan kaloriyani qayta hisoblaydi (4/9/4 kkal).
     Odam grammni to'g'irlaganda kaloriyani ham qo'lda hisoblab
     o'tirmasligi kerak. */
  function kaloriyaniHisobla() {
    const p = son(form.protein_g) ?? 0
    const y = son(form.yog_g) ?? 0
    const u = son(form.uglevod_g) ?? 0
    haptic('light')
    yangila('kaloriya', String(Math.round(p * 4 + y * 9 + u * 4)))
  }

  async function saqla() {
    const nom = form.taom_nomi.trim()
    if (!nom) return setXato('Taom nomini kiriting')

    const qiymatlar = {}
    for (const key of ['kaloriya', 'protein_g', 'yog_g', 'uglevod_g']) {
      const n = son(form[key])
      if (n === null) return setXato('Raqamlar manfiy bo\'lmasligi kerak')
      qiymatlar[key] = key === 'kaloriya' ? Math.round(n) : n
    }

    setXato(null)
    setSaqlanmoqda(true)
    try {
      const yangi = await api.updateMeal(meal.id, {
        taom_nomi: nom,
        ulush: form.ulush.trim() || null,
        ...qiymatlar,
        // Sana va vaqt o'zgarmaydi — ovqat o'z kunida qoladi.
        sana: meal.sana,
        vaqt: meal.vaqt,
      })
      haptic('success')
      onSaved?.(yangi)
      onClose()
    } catch (e) {
      haptic('error')
      setXato(e.message)
    } finally {
      setSaqlanmoqda(false)
    }
  }

  return (
    <Sheet
      open
      title="Ovqatni tahrirlash"
      onClose={onClose}
      footer={
        <button className="btn btn-primary" onClick={saqla} disabled={saqlanmoqda}>
          {saqlanmoqda ? 'Saqlanmoqda…' : 'Saqlash'}
        </button>
      }
    >
      <div className="ms-head">
        <span className="ms-thumb">
          {meal.rasm_yoli ? (
            <img src={meal.rasm_yoli} alt="" />
          ) : (
            <PlateIcon size={22} />
          )}
        </span>
        <span className="ms-meta">
          <b>{meal.taom_nomi}</b>
          <span>{vaqtQisqa(meal.vaqt)}</span>
        </span>
      </div>

      <label className="ms-field">
        <span>Taom nomi</span>
        <input
          value={form.taom_nomi}
          onChange={(e) => yangila('taom_nomi', e.target.value)}
          maxLength={160}
        />
      </label>

      <label className="ms-field">
        <span>Ulush</span>
        <input
          value={form.ulush}
          placeholder="masalan 250 g yoki 1 kosa"
          onChange={(e) => yangila('ulush', e.target.value)}
          maxLength={80}
        />
      </label>

      <div className="ms-grid">
        <label className="ms-num is-main">
          <span>Kaloriya</span>
          <input
            type="number"
            inputMode="numeric"
            value={form.kaloriya}
            onChange={(e) => yangila('kaloriya', e.target.value)}
          />
          <i>kcal</i>
        </label>

        {MAKROLAR.map(({ key, label, unit }) => (
          <label className="ms-num" key={key}>
            <span>{label}</span>
            <input
              type="number"
              inputMode="decimal"
              value={form[key]}
              onChange={(e) => yangila(key, e.target.value)}
            />
            <i>{unit}</i>
          </label>
        ))}
      </div>

      <button className="ms-calc" onClick={kaloriyaniHisobla}>
        Kaloriyani makrolardan hisoblash
      </button>

      {xato && <p className="ms-error">{xato}</p>}

      <button
        className="btn btn-danger ms-del"
        onClick={() => {
          onClose()
          onDelete?.(meal)
        }}
      >
        Ovqatni o'chirish
      </button>
    </Sheet>
  )
}
