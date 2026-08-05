import { KUN_QISQA, raqam } from '../lib/format'
import './WeeklyChart.css'

/** Haftalik kaloriya trend — ustunli diagramma + limit chizig'i. */
export default function WeeklyChart({ data }) {
  const kunlar = data?.kunlar || []
  if (!kunlar.length) return null

  const limit = data.limit || 0
  const eng_katta = Math.max(limit, ...kunlar.map((k) => k.kaloriya), 1)
  const limitFoiz = limit > 0 ? (limit / eng_katta) * 100 : 0

  return (
    <div className="wchart card">
      <div className="wchart-head">
        <div>
          <div className="wchart-title">Haftalik trend</div>
          <div className="wchart-sub">
            O'rtacha: <b>{raqam(data.ortacha_kaloriya)}</b> kcal / kun
          </div>
        </div>
      </div>

      <div className="wchart-plot">
        {/* Limit chizig'i faqat ustunlar maydonida turishi uchun alohida qatlam */}
        {limit > 0 && (
          <div className="wchart-overlay">
            <div className="wchart-limit" style={{ bottom: `${limitFoiz}%` }}>
              <span>{raqam(limit)}</span>
            </div>
          </div>
        )}

        {kunlar.map((k) => {
          const balandlik = (k.kaloriya / eng_katta) * 100
          const oshib = limit > 0 && k.kaloriya > limit
          const kun = new Date(`${k.sana}T00:00:00`)
          return (
            <div className="wchart-col" key={k.sana}>
              <div className="wchart-bar-wrap">
                <div
                  className={`wchart-bar ${oshib ? 'is-over' : ''} ${k.kaloriya === 0 ? 'is-empty' : ''}`}
                  style={{ height: `${Math.max(balandlik, k.kaloriya > 0 ? 4 : 2)}%` }}
                  title={`${raqam(k.kaloriya)} kcal`}
                />
              </div>
              <div className="wchart-label">{KUN_QISQA[kun.getDay()]}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
