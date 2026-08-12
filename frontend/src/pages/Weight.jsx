import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'
import { haptic } from '../lib/telegram'
import './Weight.css'

/** Sanani "5-avg" ko'rinishida qisqa yozadi. */
const OY_QISQA = [
  'yan', 'fev', 'mar', 'apr', 'may', 'iyn',
  'iyl', 'avg', 'sen', 'okt', 'noy', 'dek',
]

function sanaQisqa(iso) {
  const d = new Date(iso)
  return `${d.getDate()}-${OY_QISQA[d.getMonth()]}`
}

/** Oddiy chiziqli grafik — kutubxonasiz, SVG. */
function Grafik({ nuqtalar }) {
  const { yol, min, max } = useMemo(() => {
    if (!Array.isArray(nuqtalar) || nuqtalar.length < 2) {
      return { yol: '', min: 0, max: 0 }
    }

    const qiymatlar = nuqtalar.map((n) => n.vazn_kg)
    const eng_kam = Math.min(...qiymatlar)
    const eng_kop = Math.max(...qiymatlar)
    // Tekis chiziq bo'lsa ham grafik ko'rinsin.
    const oraliq = eng_kop - eng_kam || 1

    const W = 100
    const H = 40
    const yol = nuqtalar
      .map((n, i) => {
        const x = (i / (nuqtalar.length - 1)) * W
        const y = H - ((n.vazn_kg - eng_kam) / oraliq) * H
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ')

    return { yol, min: eng_kam, max: eng_kop }
  }, [nuqtalar])

  if (!Array.isArray(nuqtalar) || nuqtalar.length < 2) return null

  return (
    <div className="wgraph">
      <svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
        <path d={yol} fill="none" stroke="var(--ink)" strokeWidth="1"
              vectorEffect="non-scaling-stroke" strokeLinecap="round"
              strokeLinejoin="round" />
      </svg>
      <div className="wgraph-scale">
        <span className="num">{max.toFixed(1)}</span>
        <span className="num">{min.toFixed(1)}</span>
      </div>
    </div>
  )
}

export default function Weight({ user, onBack, onUserChange }) {
  const [royxat, setRoyxat] = useState([])
  const [qiymat, setQiymat] = useState('')
  const [saqlanmoqda, setSaqlanmoqda] = useState(false)
  const [yuklanmoqda, setYuklanmoqda] = useState(true)
  const [xato, setXato] = useState(null)

  useEffect(() => {
    api
      .getWeights()
      .then((r) => setRoyxat(Array.isArray(r) ? r : []))
      .catch(() => setRoyxat([]))
      .finally(() => setYuklanmoqda(false))
  }, [])

  async function saqla() {
    const v = parseFloat(String(qiymat).replace(',', '.'))
    if (!Number.isFinite(v) || v < 20 || v > 400) {
      setXato('Vazn 20 va 400 kg orasida bo\u2019lishi kerak')
      return
    }

    setXato(null)
    setSaqlanmoqda(true)
    haptic('light')

    try {
      const yangi = await api.addWeight(v)
      setRoyxat((old) => {
        const boshqa = old.filter((r) => r.sana !== yangi.sana)
        return [...boshqa, yangi].sort((a, b) => a.sana.localeCompare(b.sana))
      })
      setQiymat('')
      // Vazn o'zgarsa kunlik me'yor ham qayta hisoblanadi.
      const u = await api.getUser()
      onUserChange?.(u)
    } catch (e) {
      setXato(e.message)
    } finally {
      setSaqlanmoqda(false)
    }
  }

  const oxirgi = royxat.length ? royxat[royxat.length - 1] : null
  const birinchi = royxat.length ? royxat[0] : null
  const farq = oxirgi && birinchi ? oxirgi.vazn_kg - birinchi.vazn_kg : 0
  const maqsad = user?.istalgan_vazn_kg

  return (
    <div className="weight">
      <header className="weight-head">
        <button className="weight-back" onClick={onBack} aria-label="Orqaga">
          <svg viewBox="0 0 24 24" width="21" height="21">
            <path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <h1>Vazn</h1>
      </header>

      <div className="weight-body">
        <div className="wnow">
          <div className="wnow-value num">
            {oxirgi ? oxirgi.vazn_kg.toFixed(1) : (user?.joriy_vazn_kg ?? '—')}
            <span>kg</span>
          </div>
          {royxat.length > 1 && (
            <p className="wnow-delta">
              {farq === 0
                ? "O'zgarishsiz"
                : farq < 0
                  ? `${Math.abs(farq).toFixed(1)} kg kamaydi`
                  : `${farq.toFixed(1)} kg ko'paydi`}
            </p>
          )}
          {maqsad && oxirgi && Math.abs(oxirgi.vazn_kg - maqsad) > 0.1 && (
            <p className="wnow-goal">
              Maqsadgacha {Math.abs(oxirgi.vazn_kg - maqsad).toFixed(1)} kg
            </p>
          )}
        </div>

        <Grafik nuqtalar={royxat} />

        <div className="wadd">
          <input
            type="number"
            inputMode="decimal"
            step="0.1"
            placeholder="Bugungi vazn"
            value={qiymat}
            onChange={(e) => setQiymat(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && saqla()}
          />
          <button
            className="wadd-btn"
            onClick={saqla}
            disabled={!qiymat || saqlanmoqda}
          >
            Saqlash
          </button>
        </div>

        {xato && <p className="wxato">{xato}</p>}

        {royxat.length > 0 && (
          <>
            <h2 className="section-title wlist-head">Yozuvlar</h2>
            <div className="wlist">
              {[...royxat].reverse().map((r) => (
                <div className="wrow" key={r.id}>
                  <span className="wrow-date">{sanaQisqa(r.sana)}</span>
                  <span className="wrow-val num">{r.vazn_kg.toFixed(1)} kg</span>
                </div>
              ))}
            </div>
          </>
        )}

        {!yuklanmoqda && royxat.length === 0 && (
          <p className="wbosh">
            Vazningizni haftada bir marta kiriting — o'zgarishni shu yerda
            kuzatasiz.
          </p>
        )}
      </div>
    </div>
  )
}
