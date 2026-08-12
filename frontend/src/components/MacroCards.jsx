import { litr, nisbat, raqam } from '../lib/format'
import './MacroCards.css'

const MAKROLAR = [
  { key: 'protein', label: 'Oqsil', birlik: 'g' },
  { key: 'yog', label: "Yog'", birlik: 'g' },
  { key: 'uglevod', label: 'Uglevod', birlik: 'g' },
]

/**
 * Bitta dumaloq indikator.
 *
 * Chiziqli barlar o'rniga halqa: to'rttasi 2x2 to'rda yonma-yon
 * turganda ular bir oilaga o'xshaydi va asosiy kaloriya halqasi bilan
 * bitta tilda gapiradi.
 */
function MacroRing({ label, istemol, limit, birlik, oshib, format = raqam }) {
  const R = 26
  const C = 2 * Math.PI * R
  const p = Math.min(nisbat(istemol, limit), 1)

  return (
    <div className={`mring ${oshib ? 'is-over' : ''}`}>
      <div className="mring-dial">
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <circle className="mring-track" cx="32" cy="32" r={R} strokeWidth="5" />
          <circle
            className="mring-bar"
            cx="32"
            cy="32"
            r={R}
            strokeWidth="5"
            strokeDasharray={C}
            strokeDashoffset={C * (1 - p)}
            transform="rotate(-90 32 32)"
          />
        </svg>
        <span className="mring-val num">{format(istemol)}</span>
      </div>
      <span className="mring-label">{label}</span>
      <span className="mring-limit num">
        / {format(limit)} {birlik}
      </span>
    </div>
  )
}

export default function MacroCards({ summary, suvMl = 0, suvLimit = 2000 }) {
  return (
    <div className="macros">
      {MAKROLAR.map(({ key, label, birlik }) => {
        const m = summary?.[key] || { istemol: 0, limit: 0, qolgan: 0 }
        return (
          <MacroRing
            key={key}
            label={label}
            istemol={m.istemol}
            limit={m.limit}
            birlik={birlik}
            oshib={m.qolgan < 0}
          />
        )
      })}

      {/* To'rtinchi katak — suv. Ilgari alohida kartochkada edi va
          ekranni uzaytirardi.

          Millilitr emas, litr: "1 400" halqa ichiga sig'may chetidan
          chiqib ketardi, "1,4" esa bemalol turadi. */}
      <MacroRing
        label="Suv"
        istemol={suvMl}
        limit={suvLimit}
        birlik="l"
        oshib={false}
        format={litr}
      />
    </div>
  )
}
