import { MeatIcon, OilIcon, WheatIcon } from './Icons'
import { nisbat, raqam } from '../lib/format'
import './MacroCards.css'

/**
 * Uchta makro kartochkasi: oqsil, uglevod, yog'.
 *
 * Namuna dizayndagi tuzilish: tepada ikonka va QOLGAN miqdor yonma-yon,
 * ostida yorliq, eng pastda ingichka progress chizig'i.
 *
 * Suv bu yerdan olib tashlandi — namunada uchta kartochka bor va
 * to'rtinchisi qatorni siqib qo'yardi. Suv "Batafsil" oynasida qoladi.
 */
const MAKROLAR = [
  { key: 'protein', label: 'Qolgan oqsil', Icon: MeatIcon },
  { key: 'uglevod', label: 'Qolgan uglevod', Icon: WheatIcon },
  { key: 'yog', label: "Qolgan yog'lar", Icon: OilIcon },
]

function MacroCard({ label, Icon, istemol, limit }) {
  const qolgan = Math.max(0, Math.round(limit - istemol))
  const p = nisbat(istemol, limit)

  return (
    <div className="mcard">
      <div className="mcard-top">
        <Icon size={26} />
        <b className="num">{raqam(qolgan)}g</b>
      </div>
      <span className="mcard-label">{label}</span>
      <div className="mcard-bar">
        <i style={{ width: `${Math.round(p * 100)}%` }} />
      </div>
    </div>
  )
}

export default function MacroCards({ summary }) {
  return (
    <div className="macros">
      {MAKROLAR.map(({ key, label, Icon }) => {
        const m = summary?.[key] || { istemol: 0, limit: 0 }
        return (
          <MacroCard
            key={key}
            label={label}
            Icon={Icon}
            istemol={m.istemol}
            limit={m.limit}
          />
        )
      })}
    </div>
  )
}
