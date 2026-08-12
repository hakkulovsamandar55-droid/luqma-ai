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
/**
 * Ovqat qo'shish usullari — eng ko'p ishlatiladigani birinchi.
 *
 * Ilgari bular "+" atrofida yoy bo'ylab yoyilardi. Chiroyli edi, lekin
 * ishlamasdi: yorliqlar plitalar ostida turgani uchun chetdagi ikkitasi
 * bir-birini yopib qolar, eng pastdagisi ("Galereya") esa ekran qirrasi
 * ortida kesilib ketardi. Tik ro'yxatda har qanday ekran kengligida va
 * har qanday yorliq uzunligida hammasi o'qiladi.
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
