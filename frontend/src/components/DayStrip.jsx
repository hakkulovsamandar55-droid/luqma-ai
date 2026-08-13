import { useEffect, useMemo, useRef } from 'react'
import { KUN_QISQA, birXilKun } from '../lib/format'
import { haptic } from '../lib/telegram'
import './DayStrip.css'

/**
 * Gorizontal kun-tanlagich.
 *
 * Orqaga `kunlar` kun va oldinga `oldinga` kun ko'rsatiladi. Kelajakdagi
 * kunlar so'nik: ular hali kelmagan, lekin ko'rinib turgani yaxshi —
 * shunda tasma "kesilgan" bo'lib qolmaydi.
 */
export default function DayStrip({ selected, onSelect, kunlar = 14, oldinga = 3 }) {
  const scrollerRef = useRef(null)
  const activeRef = useRef(null)

  const bugun = useMemo(() => new Date(), [])

  const sanalar = useMemo(() => {
    const list = []
    for (let i = kunlar - 1; i >= -oldinga; i--) {
      const d = new Date(bugun)
      d.setDate(d.getDate() - i)
      list.push(d)
    }
    return list
  }, [bugun, kunlar, oldinga])

  // Tanlangan kunni ko'rinish maydoniga suramiz.
  useEffect(() => {
    activeRef.current?.scrollIntoView({
      behavior: 'smooth',
      inline: 'center',
      block: 'nearest',
    })
  }, [selected])

  return (
    <div className="daystrip" ref={scrollerRef}>
      {sanalar.map((d) => {
        const tanlangan = birXilKun(d, selected)
        const shuBugun = birXilKun(d, bugun)
        // Kelajak: bugundan keyingi kun (soatlarni hisobga olmasdan)
        const kelajak = d > bugun && !shuBugun
        return (
          <button
            key={d.toISOString()}
            ref={tanlangan ? activeRef : null}
            className={`day ${tanlangan ? 'is-selected' : ''} ${
              shuBugun ? 'is-today' : ''
            } ${kelajak ? 'is-future' : ''}`}
            onClick={() => {
              if (kelajak) return
              haptic('select')
              onSelect(d)
            }}
            disabled={kelajak}
            aria-pressed={tanlangan}
          >
            <span className="day-name">{KUN_QISQA[d.getDay()]}</span>
            <span className="day-num">{d.getDate()}</span>
          </button>
        )
      })}
    </div>
  )
}
