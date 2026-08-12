import { useEffect, useState } from 'react'
import {
  AiIcon,
  CameraIcon,
  GalleryIcon,
  GearIcon,
  HomeIcon,
  PencilIcon,
  PlusIcon,
  RunIcon,
  SearchIcon,
} from './Icons'
import { haptic } from '../lib/telegram'
import './TabBar.css'

/**
 * Pastki panel: Asosiy | AI | + | Mashq | Sozlamalar.
 *
 * Markazdagi "+" asosiy harakat, ikki yonida teng og'irlikdagi ikkitadan
 * bo'lim — panel simmetrik qoladi.
 */
const YOYILUVCHILAR = [
  { key: 'kamera', label: 'Kamera', Icon: CameraIcon, burchak: -90 },
  { key: 'qidiruv', label: 'Qidirish', Icon: SearchIcon, burchak: -145 },
  { key: 'galereya', label: 'Galereya', Icon: GalleryIcon, burchak: -180 },
  { key: 'matn', label: 'Yozish', Icon: PencilIcon, burchak: -35 },
]

const RADIUS = 98

export default function TabBar({ active, onNavigate, onAdd, premium, onPremium }) {
  const [ochiq, setOchiq] = useState(false)

  useEffect(() => {
    if (!ochiq) return undefined
    const onKey = (e) => e.key === 'Escape' && setOchiq(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [ochiq])

  function tanla(key) {
    haptic('light')
    setOchiq(false)
    onAdd(key)
  }

  return (
    <>
      {ochiq && <div className="fan-veil" onClick={() => setOchiq(false)} />}

      <nav className={`tabbar ${ochiq ? 'is-open' : ''}`}>
        <div className="tabbar-inner">
          <button
            className={`tab ${active === 'home' ? 'is-active' : ''}`}
            onClick={() => {
              haptic('select')
              onNavigate('home')
            }}
          >
            <span className="tab-icon">
              <HomeIcon size={23} />
            </span>
            <span>Asosiy</span>
          </button>

          <button
            className={`tab ${active === 'chat' ? 'is-active' : ''}`}
            onClick={() => {
              haptic('select')
              onNavigate('chat')
            }}
          >
            <span className="tab-icon">
              <AiIcon size={23} />
            </span>
            <span>AI</span>
          </button>

          <div className="tab-add-slot">
            {YOYILUVCHILAR.map(({ key, label, Icon, burchak }, i) => {
              const rad = (burchak * Math.PI) / 180
              return (
                <button
                  key={key}
                  className="fan-item"
                  style={{
                    '--x': `${Math.cos(rad) * RADIUS}px`,
                    '--y': `${Math.sin(rad) * RADIUS}px`,
                    '--delay': `${i * 40}ms`,
                  }}
                  tabIndex={ochiq ? 0 : -1}
                  aria-hidden={!ochiq}
                  onClick={() => tanla(key)}
                >
                  <span className="fan-icon">
                    <Icon size={21} />
                  </span>
                  <span className="fan-label">{label}</span>
                </button>
              )
            })}

            <button
              className="tab-add"
              onClick={() => {
                haptic('medium')
                // Ovqat tahlili premium bilan ishlaydi — premiumsiz
                // foydalanuvchiga menyu ko'rsatib keyin "mumkin emas"
                // deyish o'rniga darhol obuna oynasini ochamiz.
                if (!premium) {
                  onPremium()
                  return
                }
                setOchiq((v) => !v)
              }}
              aria-label={ochiq ? 'Yopish' : "Ovqat qo'shish"}
              aria-expanded={ochiq}
            >
              <PlusIcon size={26} />
            </button>
          </div>

          <button
            className={`tab ${active === 'mashq' ? 'is-active' : ''}`}
            onClick={() => {
              haptic('select')
              onNavigate('mashq')
            }}
          >
            <span className="tab-icon">
              <RunIcon size={23} />
            </span>
            <span>Mashq</span>
          </button>

          <button
            className={`tab ${active === 'settings' ? 'is-active' : ''}`}
            onClick={() => {
              haptic('select')
              onNavigate('settings')
            }}
          >
            <span className="tab-icon">
              <GearIcon size={23} />
            </span>
            <span>Sozlamalar</span>
          </button>
        </div>
      </nav>
    </>
  )
}
