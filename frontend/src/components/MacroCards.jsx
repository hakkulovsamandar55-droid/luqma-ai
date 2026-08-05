import { ProteinIcon, CarbsIcon, FatIcon } from './Icons'
import { nisbat, raqam } from '../lib/format'
import './MacroCards.css'

const MAKROLAR = [
  { key: 'protein', label: 'Oqsil', Icon: ProteinIcon, tur: 'protein' },
  { key: 'uglevod', label: 'Uglevod', Icon: CarbsIcon, tur: 'carbs' },
  { key: 'yog', label: "Yog'", Icon: FatIcon, tur: 'fat' },
]

/** Uchta teng kartochka: qolgan oqsil / uglevod / yog' + progress-bar. */
export default function MacroCards({ summary }) {
  return (
    <div className="macros">
      {MAKROLAR.map(({ key, label, Icon, tur }) => {
        const m = summary?.[key] || { istemol: 0, limit: 0, qolgan: 0 }
        const oshib = m.qolgan < 0
        return (
          <div className={`macro macro--${tur}`} key={key}>
            <div className="macro-icon">
              <Icon size={17} />
            </div>
            <div className={`macro-value ${oshib ? 'is-over' : ''}`}>
              {oshib ? '+' : ''}
              {raqam(Math.abs(m.qolgan))}
              <span className="macro-unit">g</span>
            </div>
            <div className="macro-label">Qolgan {label.toLowerCase()}</div>
            <div className="macro-bar">
              <span
                className={oshib ? 'is-over' : ''}
                style={{ width: `${nisbat(m.istemol, m.limit) * 100}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
