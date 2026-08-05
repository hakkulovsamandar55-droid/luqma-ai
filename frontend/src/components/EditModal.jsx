import { useEffect, useState } from 'react'
import Sheet from './Sheet'
import { haptic } from '../lib/telegram'
import './EditModal.css'

/**
 * Bitta profil maydonini tahrirlash uchun universal modal.
 * field: { key, label, type: 'number'|'text'|'choice', unit, options, min, max, hint }
 */
export default function EditModal({ field, value, onSave, onClose }) {
  const [qiymat, setQiymat] = useState(value ?? '')
  const [saqlanmoqda, setSaqlanmoqda] = useState(false)
  const [xato, setXato] = useState(null)

  useEffect(() => setQiymat(value ?? ''), [value, field])

  if (!field) return null

  async function saqla(yangi = qiymat) {
    setXato(null)

    let tayyor = yangi
    if (field.type === 'number') {
      tayyor = Number(String(yangi).replace(',', '.'))
      if (!Number.isFinite(tayyor)) {
        setXato('Raqam kiriting')
        return
      }
      if (field.min != null && tayyor < field.min) {
        setXato(`Eng kichik qiymat: ${field.min}`)
        return
      }
      if (field.max != null && tayyor > field.max) {
        setXato(`Eng katta qiymat: ${field.max}`)
        return
      }
    } else if (field.type === 'text') {
      tayyor = String(yangi).trim()
      if (!tayyor) {
        setXato("Bo'sh qoldirib bo'lmaydi")
        return
      }
    }

    setSaqlanmoqda(true)
    try {
      await onSave(field.key, tayyor)
      haptic('success')
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
      title={field.label}
      onClose={onClose}
      footer={
        field.type !== 'choice' && (
          <button className="btn btn-primary" onClick={() => saqla()} disabled={saqlanmoqda}>
            {saqlanmoqda ? 'Saqlanmoqda...' : 'Saqlash'}
          </button>
        )
      }
    >
      {field.type === 'choice' ? (
        <div className="em-choices">
          {field.options.map((opt) => (
            <button
              key={opt.value}
              className={`em-choice ${qiymat === opt.value ? 'is-on' : ''}`}
              disabled={saqlanmoqda}
              onClick={() => {
                setQiymat(opt.value)
                saqla(opt.value)
              }}
            >
              <span className="em-choice-text">
                <b>{opt.label}</b>
                {opt.hint && <small>{opt.hint}</small>}
              </span>
              <span className="em-radio" />
            </button>
          ))}
        </div>
      ) : (
        <div className="em-input-wrap">
          <input
            className="em-input"
            type={field.type === 'number' ? 'number' : 'text'}
            inputMode={field.type === 'number' ? 'decimal' : 'text'}
            autoFocus
            value={qiymat}
            placeholder={field.placeholder}
            onChange={(e) => setQiymat(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && saqla()}
          />
          {field.unit && <span className="em-unit">{field.unit}</span>}
        </div>
      )}

      {field.hint && <p className="em-hint">{field.hint}</p>}
      {xato && <p className="em-error">{xato}</p>}
    </Sheet>
  )
}
