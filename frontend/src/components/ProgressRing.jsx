import { useEffect, useRef, useState } from 'react'
import { raqam } from '../lib/format'
import './ProgressRing.css'

/**
 * Katta dumaloq progress-ring — ichida qolgan kaloriya raqami.
 * Halqa 0 dan joriy qiymatgacha animatsiya bilan to'ladi.
 */
export default function ProgressRing({
  istemol = 0,
  limit = 2000,
  size = 224,
  strokeWidth = 16,
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  const oshib = istemol > limit
  const nisbat = limit > 0 ? Math.min(istemol / limit, 1) : 0
  const qolgan = Math.round(limit - istemol)

  // Birinchi renderda 0 dan boshlab animatsiya qilamiz.
  const [progress, setProgress] = useState(0)
  const kadr = useRef()

  useEffect(() => {
    cancelAnimationFrame(kadr.current)
    kadr.current = requestAnimationFrame(() => setProgress(nisbat))
    return () => cancelAnimationFrame(kadr.current)
  }, [nisbat])

  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} aria-hidden="true">
        <circle
          className="ring-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className={`ring-bar ${oshib ? 'is-over' : ''}`}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>

      <div className="ring-center">
        <div className={`ring-value ${oshib ? 'is-over' : ''}`}>
          {raqam(Math.abs(qolgan))}
        </div>
        <div className="ring-label">
          {oshib ? 'Kaloriya oshib ketdi' : 'Qolgan kaloriya'}
        </div>
        <div className="ring-sub">
          {raqam(istemol)} / {raqam(limit)} kcal
        </div>
      </div>
    </div>
  )
}
