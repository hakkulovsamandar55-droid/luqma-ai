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
  const { yol, toldirish, oxirgi, min, max } = useMemo(() => {
    if (!Array.isArray(nuqtalar) || nuqtalar.length < 2) {
      return { yol: '', toldirish: '', oxirgi: [0, 0], min: 0, max: 0 }
    }

    const qiymatlar = nuqtalar.map((n) => n.vazn_kg)
    const eng_kam = Math.min(...qiymatlar)
    const eng_kop = Math.max(...qiymatlar)
    // Tekis chiziq bo'lsa ham grafik ko'rinsin.
    const oraliq = eng_kop - eng_kam || 1

    // Chekka bo'sh joy: chiziq kartochka qirrasiga tegib turmasligi kerak,
    // aks holda u grafik emas, tasodifan chizilgandek ko'rinadi.
    const W = 100
    const H = 40
    const PX = 3
    const PY = 5

    const koord = nuqtalar.map((n, i) => {
      const x = PX + (i / (nuqtalar.length - 1)) * (W - PX * 2)
      const y =
        H - PY - ((n.vazn_kg - eng_kam) / oraliq) * (H - PY * 2)
      return [Number(x.toFixed(2)), Number(y.toFixed(2))]
    })

    const yol = koord
      .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`)
      .join(' ')

    // To'ldirish uchun yopiq shakl — chiziq ostidagi maydon.
    const [oxirgiX] = koord[koord.length - 1]
    const toldirish = `${yol} L${oxirgiX},${H} L${koord[0][0]},${H} Z`

    return { yol, toldirish, oxirgi: koord[koord.length - 1], min: eng_kam, max: eng_kop }
  }, [nuqtalar])

  if (!Array.isArray(nuqtalar) || nuqtalar.length < 2) return null

  return (
    <div className="wgraph">
      {/* preserveAspectRatio="none" ataylab: grafik kartochka kengligiga
          cho'ziladi. Shu sababli chiziq qalinligi va nuqta radiusi
          non-scaling-stroke bilan himoyalangan. */}
      <div className="wgraph-plot">
      <svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id="wgrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={toldirish} fill="url(#wgrad)" stroke="none" />
        <path d={yol} fill="none" stroke="var(--accent)" strokeWidth="2"
              vectorEffect="non-scaling-stroke" strokeLinecap="round"
              strokeLinejoin="round" />
      </svg>

      {/* Oxirgi o'lchov — alohida belgilanadi, chunki "hozir qayerdaman"
          degan savolga aynan shu javob beradi. */}
      <span
        className="wgraph-dot"
        style={{ left: `${oxirgi[0]}%`, top: `${(oxirgi[1] / 40) * 100}%` }}
      />
      </div>
      {/* Eng katta qiymat o'ngda tepada, eng kichigi chapda pastda:
          ikkalasi ham o'ng tomonda turganda pastdagisi chiziqning
          oxirgi nuqtasi bilan ustma-ust tushib qolardi. */}
      <span className="wgraph-max num">{max.toFixed(1)}</span>
      <span className="wgraph-min num">{min.toFixed(1)}</span>
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
