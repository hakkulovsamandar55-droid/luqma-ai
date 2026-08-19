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
 * Pastki panel: Asosiy | Mashq | + | AI | Sozlamalar.
 *
 * DIQQAT: "+" tugmasi va yoyiluvchi menyu `.tabbar-inner` DAN TASHQARIDA
 * turadi — svg fon boshqa qatlamda, bu esa tugmani panel tepasiga
 * chiqishiga (notch ustiga suzishiga) imkon beradi.
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
        {/* Referensdagi aynan o'zi: to'lqinsimon panel foni SVG path
            bilan chizilgan (CSS mask emas), markazda "+" uchun o'yiq.
            Bizda referensdagi 3 tadan (Asosiy/+/Sozlamalar) ko'proq —
            5 ta tugma bor, shuning uchun qo'shimcha ikkitasi (AI, Mashq)
            ikki chetga simmetrik qo'yildi. */}
        <svg className="tabbar-bg" viewBox="0 0 390 92" preserveAspectRatio="none" aria-hidden="true">
          <path d="M0 30C0 16 11 5 25 5h104c9 0 16 6 19 14 5 16 20 27 37 27s32-11 37-27c3-8 10-14 19-14h104c14 0 25 11 25 25v62H0V30Z" />
        </svg>

        <div className="tabbar-inner">
          <Tab nom="Asosiy" belgi="home" Icon={HomeIcon} />
          <Tab nom="Mashq" belgi="mashq" Icon={RunIcon} />
          <div className="tab-add-slot" aria-hidden="true" />
          <Tab nom="AI" belgi="chat" Icon={AiIcon} />
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
          <PlusIcon size={32} />
        </button>
      </nav>
    </>
  )
}
