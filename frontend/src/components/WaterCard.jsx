import { WaterIcon } from './Icons'
import { nisbat, raqam } from '../lib/format'
import { haptic } from '../lib/telegram'
import './WaterCard.css'

const STAKAN_ML = 250

/** Suv ichish tracker — stakanlar qatori. */
export default function WaterCard({ suvMl = 0, limitMl = 2000, onChange, disabled }) {
  const stakanlar = Math.max(1, Math.round(limitMl / STAKAN_ML))
  const ichilgan = Math.round(suvMl / STAKAN_ML)

  return (
    <div className="water card">
      <div className="water-head">
        <div className="water-icon">
          <WaterIcon size={17} />
        </div>
        <div className="water-titles">
          <div className="water-title">Suv</div>
          <div className="water-sub">
            {raqam(suvMl)} / {raqam(limitMl)} ml
          </div>
        </div>
        <div className="water-actions">
          <button
            className="water-btn"
            disabled={disabled || suvMl <= 0}
            onClick={() => {
              haptic('light')
              onChange(-STAKAN_ML)
            }}
            aria-label="Kamaytirish"
          >
            −
          </button>
          <button
            className="water-btn is-primary"
            disabled={disabled}
            onClick={() => {
              haptic('light')
              onChange(STAKAN_ML)
            }}
            aria-label="Stakan qo'shish"
          >
            +
          </button>
        </div>
      </div>

      <div className="water-glasses">
        {Array.from({ length: Math.min(stakanlar, 12) }, (_, i) => (
          <span key={i} className={`glass ${i < ichilgan ? 'is-full' : ''}`} />
        ))}
      </div>

      <div className="water-bar">
        <span style={{ width: `${nisbat(suvMl, limitMl) * 100}%` }} />
      </div>
    </div>
  )
}
