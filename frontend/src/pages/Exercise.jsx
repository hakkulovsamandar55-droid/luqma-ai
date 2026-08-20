import { useCallback, useEffect, useState } from 'react'
import Sheet from '../components/Sheet'
import { DownloadIcon, PlayIcon } from '../components/Icons'
import { api } from '../lib/api'
import { raqam } from '../lib/format'
import { haptic, showAlert } from '../lib/telegram'
import './Exercise.css'

const DARAJALAR = [
  { key: '', label: 'Hammasi' },
  { key: 'boshlangich', label: 'Boshlang\u2019ich' },
  { key: 'orta', label: "O'rta" },
  { key: 'yuqori', label: 'Yuqori' },
]

const TURKUM_NOMI = {
  kuch: 'Kuch',
  chozilish: "Cho'zilish",
  harakatchanlik: 'Harakatchanlik',
  umumiy: 'Umumiy',
}

function vaqt(sek) {
  if (sek >= 60) {
    const d = Math.round(sek / 60)
    return `${d} daq`
  }
  return `${sek} son`
}

export default function Exercise({ onBack }) {
  const [royxat, setRoyxat] = useState([])
  const [loglar, setLoglar] = useState([])
  const [daraja, setDaraja] = useState('')
  const [ochiq, setOchiq] = useState(null)
  const [yuklanmoqda, setYuklanmoqda] = useState(true)
  const [ish, setIsh] = useState(false)

  const yukla = useCallback(() => {
    setYuklanmoqda(true)
    Promise.all([
      api.getExercises(daraja ? { daraja } : {}).catch(() => []),
      api.getExerciseLogs().catch(() => []),
    ])
      .then(([e, l]) => {
        setRoyxat(Array.isArray(e) ? e : [])
        setLoglar(Array.isArray(l) ? l : [])
      })
      .finally(() => setYuklanmoqda(false))
  }, [daraja])

  useEffect(yukla, [yukla])

  async function bajardim(ex) {
    setIsh(true)
    haptic('light')
    try {
      await api.logExercise({ exercise_id: ex.id })
      setOchiq(null)
      yukla()
    } catch (e) {
      showAlert(e.message)
    } finally {
      setIsh(false)
    }
  }

  // Bugungi yakun — foydalanuvchi nima qilganini ko'rsin.
  const jamiVaqt = loglar.reduce((s, l) => s + (l.davomiylik_sek || 0), 0)
  const jamiKcal = loglar.reduce((s, l) => s + (l.kaloriya || 0), 0)

  return (
    <div className="exr">
      <header className="exr-head">
        <button className="exr-back" onClick={onBack} aria-label="Orqaga">
          <svg viewBox="0 0 24 24" width="21" height="21">
            <path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <div>
          <h1>Mashq</h1>
          <p>Harakat — kunlik odat</p>
        </div>
      </header>

      <div className="exr-body">
        {/* Bugungi yakun. Vazn yoki tashqi ko'rinish emas — bajarilgan
            ish va izchillik ko'rsatiladi. */}
        <div className="exr-today">
          <div>
            <b className="num">{loglar.length}</b>
            <span>bugun bajarildi</span>
          </div>
          <div>
            <b className="num">{vaqt(jamiVaqt)}</b>
            <span>harakat</span>
          </div>
          <div>
            <b className="num">{raqam(jamiKcal)}</b>
            <span>kcal</span>
          </div>
        </div>

        <div className="exr-filters">
          {DARAJALAR.map((d) => (
            <button
              key={d.key}
              className={`exr-filter ${daraja === d.key ? 'is-on' : ''}`}
              onClick={() => {
                haptic('light')
                setDaraja(d.key)
              }}
            >
              {d.label}
            </button>
          ))}
        </div>

        {yuklanmoqda && royxat.length === 0 ? (
          <p className="exr-bosh">Yuklanmoqda…</p>
        ) : royxat.length === 0 ? (
          <p className="exr-bosh">
            Hozircha mashq qo'shilmagan. Keyinroq urinib ko'ring.
          </p>
        ) : (
          <div className="exr-list">
            {royxat.map((ex) => (
              <button
                key={ex.id}
                className="exr-card"
                onClick={() => {
                  haptic('light')
                  setOchiq(ex)
                }}
              >
                <span className="exr-play" aria-hidden="true">
                  <PlayIcon size={17} />
                </span>
                <span className="exr-card-txt">
                  <b>{ex.nom}</b>
                  <span>
                    {TURKUM_NOMI[ex.turkum] || ex.turkum} ·{' '}
                    {ex.takror || vaqt(ex.davomiylik_sek)}
                  </span>
                </span>
                <span className="exr-chev">›</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <Sheet open={Boolean(ochiq)} title={ochiq?.nom} onClose={() => setOchiq(null)}>
        {ochiq && (
          <>
            {ochiq.video_url ? (
              <video
                className="exr-video"
                src={ochiq.video_url}
                poster={ochiq.rasm_url || undefined}
                controls
                playsInline
                preload="none"
              />
            ) : (
              <div className="exr-novideo">
                <PlayIcon size={22} />
                <span>Video hozircha yo'q</span>
              </div>
            )}

            <div className="exr-meta">
              <div>
                <span>Davomiyligi</span>
                <b>{ochiq.takror || vaqt(ochiq.davomiylik_sek)}</b>
              </div>
              <div>
                <span>Daraja</span>
                <b>
                  {DARAJALAR.find((d) => d.key === ochiq.daraja)?.label ||
                    ochiq.daraja}
                </b>
              </div>
              <div>
                <span>Taxminan</span>
                <b className="num">{raqam(ochiq.kaloriya)} kcal</b>
              </div>
            </div>

            {ochiq.tavsif && <p className="exr-desc">{ochiq.tavsif}</p>}

            <button
              className="btn btn-primary exr-done"
              disabled={ish}
              onClick={() => bajardim(ochiq)}
            >
              Bajardim
            </button>

            {ochiq.video_url && (
              <a
                className="exr-dl"
                href={ochiq.video_url}
                target="_blank"
                rel="noreferrer"
                download
              >
                <DownloadIcon size={17} />
                Videoni yuklab olish
              </a>
            )}
          </>
        )}
      </Sheet>
    </div>
  )
}
