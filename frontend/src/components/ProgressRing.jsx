import { useEffect, useRef, useState } from 'react'
import { FireIcon, TargetIcon } from './Icons'
import { raqam } from '../lib/format'
import useCountUp from '../lib/useCountUp'
import './ProgressRing.css'

/**
 * Bosh ekranning "hero" elementi — gradientli progress halqa.
 * Ichida: ikonka, katta raqam, label va maqsad foizi.
 */
export default function ProgressRing({
  istemol = 0,
  limit = 2000,
  size = 240,
  strokeWidth = 18,
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  const oshib = istemol > limit
  const nisbat = limit > 0 ? Math.min(istemol / limit, 1) : 0
  const foiz = limit > 0 ? Math.round((istemol / limit) * 100) : 0
  const qolgan = Math.round(limit - istemol)

  // Halqa 0 dan joriy qiymatgacha to'ladi, raqam esa sanab chiqadi.
  const [progress, setProgress] = useState(0)
  const kadr = useRef()
  const korsatilgan = useCountUp(Math.abs(qolgan))
  const korsatilganFoiz = useCountUp(foiz)

  useEffect(() => {
    cancelAnimationFrame(kadr.current)
    kadr.current = requestAnimationFrame(() => setProgress(nisbat))
    return () => cancelAnimationFrame(kadr.current)
  }, [nisbat])

  const Icon = oshib ? TargetIcon : FireIcon

  return (
    <div className={`ring ${oshib ? 'is-over' : ''}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} aria-hidden="true">
        <defs>
          <linearGradient id="ring-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b72ff" />
            <stop offset="55%" stopColor="#6b4eff" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
          <linearGradient id="ring-grad-over" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ff8a8d" />
            <stop offset="100%" stopColor="#e8474b" />
          </linearGradient>
        </defs>

        <circle
          className="ring-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="ring-bar"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          stroke={`url(#${oshib ? 'ring-grad-over' : 'ring-grad'})`}
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress)}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>

      <div className="ring-center">
        <div className="ring-badge">
          <Icon size={19} />
        </div>
        <div className="ring-value">
          {oshib && <span className="ring-plus">+</span>}
          {raqam(korsatilgan)}
        </div>
        <div className="ring-label">
          {oshib ? 'Kaloriya oshib ketdi' : 'Qolgan kaloriya'}
        </div>
        <div className="ring-sub">
          Bugungi maqsadning <b>{Math.round(korsatilganFoiz)}%</b>
        </div>
      </div>
    </div>
  )
}
