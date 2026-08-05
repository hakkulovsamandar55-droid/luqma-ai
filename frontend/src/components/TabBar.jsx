import { GearIcon, HomeIcon, PlusIcon } from './Icons'
import { haptic } from '../lib/telegram'
import './TabBar.css'

/** Pastki fixed tab-bar: Home | katta floating '+' | Sozlamalar. */
export default function TabBar({ active, onNavigate, onAdd }) {
  return (
    <nav className="tabbar">
      <div className="tabbar-inner">
        <button
          className={`tab ${active === 'home' ? 'is-active' : ''}`}
          onClick={() => {
            haptic('select')
            onNavigate('home')
          }}
          aria-label="Bosh sahifa"
        >
          <span className="tab-icon">
            <HomeIcon size={27} />
          </span>
          <span>Asosiy</span>
        </button>

        <button
          className="tab-add"
          onClick={() => {
            haptic('medium')
            onAdd()
          }}
          aria-label="Ovqat qo'shish"
        >
          <PlusIcon size={28} />
        </button>

        <button
          className={`tab ${active === 'settings' ? 'is-active' : ''}`}
          onClick={() => {
            haptic('select')
            onNavigate('settings')
          }}
          aria-label="Sozlamalar"
        >
          <span className="tab-icon">
            <GearIcon size={27} />
          </span>
          <span>Sozlamalar</span>
        </button>
      </div>
    </nav>
  )
}
