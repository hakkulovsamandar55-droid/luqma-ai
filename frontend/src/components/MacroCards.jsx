import { ProteinIcon, CarbsIcon, FatIcon } from './Icons'
import { nisbat, raqam } from '../lib/format'
import useCountUp from '../lib/useCountUp'
import './MacroCards.css'

const MAKROLAR = [
  { key: 'protein', label: 'Oqsil', Icon: ProteinIcon, tur: 'protein' },
  { key: 'uglevod', label: 'Uglevod', Icon: CarbsIcon, tur: 'carbs' },
  { key: 'yog', label: "Yog'", Icon: FatIcon, tur: 'fat' },
]

function MacroCard({ label, Icon, tur, m, kechikish }) {
  const oshib = m.qolgan < 0
  const foiz = Math.round(nisbat(m.istemol, m.limit) * 100)
  const korsatilgan = useCountUp(Math.abs(m.qolgan))

  return (
    <div
      className={`macro macro--${tur} ${oshib ? 'is-over' : ''} fade-up`}
      style={{ animationDelay: `${kechikish}ms` }}
    >
      <div className="macro-icon">
        <Icon size={16} />
      </div>

      <div className="macro-value">
        {oshib && '+'}
        {raqam(korsatilgan)}
        <span className="macro-unit">g</span>
      </div>
      {/* Faqat makro nomi — "Qolgan" halqadagi yozuvdan tushunarli, uch
          ustunga sig'maydi va kesilib qoladi. */}
      <div className="macro-label">{label}</div>

      <div className="macro-foot">
        <div className="macro-bar">
          <span style={{ width: `${foiz}%` }} />
        </div>
        <span className="macro-pct">{foiz}%</span>
      </div>
    </div>
  )
}

/** Uchta teng kartochka: qolgan oqsil / uglevod / yog'. */
export default function MacroCards({ summary }) {
  return (
    <div className="macros">
      {MAKROLAR.map(({ key, label, Icon, tur }, i) => (
        <MacroCard
          key={key}
          label={label}
          Icon={Icon}
          tur={tur}
          kechikish={80 + i * 70}
          m={summary?.[key] || { istemol: 0, limit: 0, qolgan: 0 }}
        />
      ))}
    </div>
  )
}
