import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import './Chat.css'

const TAYYOR_SAVOLLAR = [
  'Kechqurun nima yesam?',
  'Nega vaznim tushmayapti?',
  'Kunduzi och qolyapman',
  "Non yesam bo'ladimi?",
]

/**
 * Murabbiy bilan suhbat.
 *
 * Ko'rinishi ataylab Telegram chatiga o'xshaydi — foydalanuvchi bu
 * naqshni allaqachon biladi, o'rganishi shart emas.
 */
export default function Chat({ onBack }) {
  const [xabarlar, setXabarlar] = useState([])
  const [matn, setMatn] = useState('')
  const [kutilmoqda, setKutilmoqda] = useState(false)
  const [yuklanmoqda, setYuklanmoqda] = useState(true)
  const [xato, setXato] = useState(null)

  const oxiriRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    api
      .getChatHistory()
      .then((r) => setXabarlar(Array.isArray(r) ? r : []))
      .catch(() => setXabarlar([]))
      .finally(() => setYuklanmoqda(false))
  }, [])

  useEffect(() => {
    oxiriRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [xabarlar, kutilmoqda])

  async function yubor(savol) {
    const q = (savol ?? matn).trim()
    if (!q || kutilmoqda) return

    haptic('light')
    setMatn('')
    setXato(null)
    setXabarlar((x) => [...x, { rol: 'user', matn: q, id: `l${Date.now()}` }])
    setKutilmoqda(true)

    try {
      const javob = await api.sendChat(q)
      setXabarlar((x) => [
        ...x,
        { rol: 'murabbiy', matn: javob.matn, id: javob.id || `a${Date.now()}` },
      ])
    } catch (e) {
      setXato(e.message || "Javob kelmadi, qayta urinib ko'ring")
    } finally {
      setKutilmoqda(false)
    }
  }

  function osish(el) {
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 104)}px`
  }

  const bosh = !yuklanmoqda && xabarlar.length === 0

  return (
    <div className="chat">
      <header className="chat-head">
        <button className="chat-back" onClick={onBack} aria-label="Orqaga">
          <svg viewBox="0 0 24 24" width="21" height="21">
            <path
              d="M15 18l-6-6 6-6"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
        <div>
          <h1>Murabbiy</h1>
          <p>Sizning kuningizni biladi</p>
        </div>
      </header>

      <div className="chat-msgs">
        {bosh && (
          <div className="msg is-ai">
            Salom! Bugungi ovqatlanishingizni ko'rib turibman. Nima haqida
            gaplashamiz?
          </div>
        )}

        {xabarlar.map((m) => (
          <div
            key={m.id}
            className={`msg ${m.rol === 'user' ? 'is-me' : 'is-ai'}`}
          >
            {m.matn}
          </div>
        ))}

        {kutilmoqda && (
          <div className="msg-dots" aria-label="Javob yozilmoqda">
            <i />
            <i />
            <i />
          </div>
        )}

        {xato && <div className="chat-error">{xato}</div>}

        <div ref={oxiriRef} />
      </div>

      {bosh && (
        <div className="chat-chips">
          {TAYYOR_SAVOLLAR.map((s) => (
            <button key={s} className="chip" onClick={() => yubor(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="chat-compose">
        <textarea
          ref={inputRef}
          rows={1}
          value={matn}
          placeholder="Savolingizni yozing…"
          maxLength={1000}
          onChange={(e) => {
            setMatn(e.target.value)
            osish(e.target)
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              yubor()
            }
          }}
        />
        <button
          className="chat-send"
          onClick={() => yubor()}
          disabled={!matn.trim() || kutilmoqda}
          aria-label="Yuborish"
        >
          <svg viewBox="0 0 24 24" width="19" height="19">
            <path
              d="M12 19V5M5 12l7-7 7 7"
              fill="none"
              stroke="#fff"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
    </div>
  )
}
