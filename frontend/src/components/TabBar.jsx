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
 * DIQQAT: "+" tugmasi va yoyiluvchi menyu `.tabbar-inner` DAN TASHQARIDA
 * turadi. Sabab: o'yiq CSS mask bilan qilingan, mask esa ichidagi
 * hamma narsani qirqadi — tugma panel tepasiga chiqa olmasdi.
 */
const YOYILUVCHILAR = [
  { key: 'kamera', label: 'Kamera', Icon: CameraIcon },
  { key: 'galereya', label: 'Galereya', Icon: GalleryIcon },
  { key: 'qidiruv', label: 'Qidirish', Icon: SearchIcon },
  { key: 'matn', label: 'Yozish', Icon: PencilIcon },
]

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

  const Tab = ({ nom, belgi, Icon }) => (
    <button
      className={`tab ${active === belgi ? 'is-active' : ''}`}
      onClick={() => {
        haptic('select')
        onNavigate(belgi)
      }}
      aria-label={nom}
    >
      <span className="tab-icon">
        <Icon size={26} />
      </span>
      <span>{nom}</span>
    </button>
  )

  return (
    <>
      {ochiq && <div className="fan-veil" onClick={() => setOchiq(false)} />}

      <nav className={`tabbar ${ochiq ? 'is-open' : ''}`}>
        <div className="tabbar-inner">
          <Tab nom="Asosiy" belgi="home" Icon={HomeIcon} />
          <Tab nom="AI" belgi="chat" Icon={AiIcon} />
          <div className="tab-add-slot" aria-hidden="true" />
          <Tab nom="Mashq" belgi="mashq" Icon={RunIcon} />
          <Tab nom="Sozlamalar" belgi="settings" Icon={GearIcon} />
        </div>

        <div className="fan">
          {YOYILUVCHILAR.map(({ key, label, Icon }, i) => (
            <button
              key={key}
              className="fan-item"
              style={{ '--delay': `${i * 45}ms` }}
              tabIndex={ochiq ? 0 : -1}
              aria-hidden={!ochiq}
              onClick={() => tanla(key)}
            >
              <span className="fan-icon">
                <Icon size={20} />
              </span>
              <span className="fan-label">{label}</span>
            </button>
          ))}
        </div>

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
          <PlusIcon size={28} />
        </button>
      </nav>
    </>
  )
}
