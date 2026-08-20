import { useMemo } from 'react'
import { KUN_QISQA, birXilKun } from '../lib/format'
import { haptic } from '../lib/telegram'
import './DayStrip.css'

/**
 * Haftalik kun-tanlagich — referensdagi aynan o'zi: joriy haftaning
 * Dushanba-Shanba kunlari (6 ustun, Yakshanba yo'q), skroll qilinmaydi.
 */
export default function DayStrip({ selected, onSelect }) {
  const bugun = useMemo(() => new Date(), [])

  const sanalar = useMemo(() => {
    const dushanba = new Date(bugun)
    const surilish = (bugun.getDay() + 6) % 7 // Dushanbagacha orqaga
    dushanba.setDate(bugun.getDate() - surilish)

    const list = []
    for (let i = 0; i < 6; i++) {
      const d = new Date(dushanba)
      d.setDate(dushanba.getDate() + i)
      list.push(d)
    }
    return list
  }, [bugun])

  return (
    <div className="daystrip">
      {sanalar.map((d) => {
        const tanlangan = birXilKun(d, selected)
        const shuBugun = birXilKun(d, bugun)
        const kelajak = d > bugun && !shuBugun
        return (
          <button
            key={d.toISOString()}
            className={`day ${tanlangan ? 'is-selected' : ''} ${
              kelajak ? 'is-future' : ''
            }`}
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
