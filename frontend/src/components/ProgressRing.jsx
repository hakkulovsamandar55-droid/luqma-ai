import { useEffect, useRef, useState } from 'react'
import { raqam } from '../lib/format'
import useCountUp from '../lib/useCountUp'
import './ProgressRing.css'

/**
 * Bosh ekranning asosiy elementi.
 *
 * Ataylab sodda: bitta ingichka halqa, katta raqam va ostida oddiy
 * tildagi jumla. Halqa va raqam faqat me'yordan oshganda qizaradi —
 * ilovada rang shundan boshqa hech narsani bildirmaydi.
 */
/**
 * O'lcham CSS dan keladi (viewBox + foizli kenglik), piksel emas.
 * Sabab: Home ekrani skroll qilinmaydi, shuning uchun halqa mavjud
 * balandlikka moslashishi kerak — aks holda kichik telefonlarda
 * kontent bir-birining ustiga chiqadi.
 */
export default function ProgressRing({ istemol = 0, limit = 2000 }) {
  const VIEW = 200
  const strokeWidth = 9
  const radius = (VIEW - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius

  const oshib = istemol > limit
  const nisbat = limit > 0 ? Math.min(istemol / limit, 1) : 0
  const qolgan = Math.round(limit - istemol)

  const [progress, setProgress] = useState(0)
  const kadr = useRef()
  const korsatilgan = useCountUp(Math.abs(qolgan))

  useEffect(() => {
    cancelAnimationFrame(kadr.current)
    kadr.current = requestAnimationFrame(() => setProgress(nisbat))
    return () => cancelAnimationFrame(kadr.current)
  }, [nisbat])

  return (
    <div className={`ring-wrap ${oshib ? 'is-over' : ''}`}>
      <div className="ring">
        <svg viewBox={`0 0 ${VIEW} ${VIEW}`} aria-hidden="true">
          <circle
            className="ring-track"
            cx={VIEW / 2}
            cy={VIEW / 2}
            r={radius}
            strokeWidth={strokeWidth}
          />
          <circle
            className="ring-bar"
            cx={VIEW / 2}
            cy={VIEW / 2}
            r={radius}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - progress)}
            transform={`rotate(-90 ${VIEW / 2} ${VIEW / 2})`}
          />

          {/* Progress uchidagi nuqta — halqa bo'ylab yuradi */}
          <circle
            className="ring-dot"
            cx={VIEW / 2}
            cy={strokeWidth / 2}
            r={strokeWidth / 2}
            style={{
              transform: `rotate(${progress * 360}deg)`,
              transformOrigin: `${VIEW / 2}px ${VIEW / 2}px`,
              opacity: progress > 0.02 ? 1 : 0,
            }}
          />
        </svg>

        <div className="ring-center">
          <div className="ring-value num">{raqam(korsatilgan)}</div>
          <div className="ring-label">
            {oshib ? 'kcal oshdi' : 'kcal qoldi'}
          </div>
          {/* Foiz — raqamning ma'nosini bir qarashda beradi.
              Ataylab kichik: asosiy langar katta raqam bo'lib qolsin. */}
          <div className="ring-pct num">{Math.round(nisbat * 100)}%</div>
        </div>
      </div>

      {/* Raqamning ma'nosi so'z bilan ham yozilgan — hech kim
          tushuntirmasdan tushunishi uchun. */}
      <p className="ring-line">
        {oshib ? (
          <>
            Me'yordan <b>{raqam(Math.abs(qolgan))} kcal</b> oshib ketdingiz
          </>
        ) : (
          <>
            Bugun yana <b>{raqam(qolgan)} kcal</b> yeyishingiz mumkin
          </>
        )}
      </p>
    </div>
  )
}
