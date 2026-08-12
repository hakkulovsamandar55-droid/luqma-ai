import { useCallback, useEffect, useState } from 'react'
import TabBar from './components/TabBar'
import AddMeal from './pages/AddMeal'
import Admin from './pages/Admin'
import Chat from './pages/Chat'
import Exercise from './pages/Exercise'
import Home from './pages/Home'
import Onboarding from './pages/Onboarding'
import Premium from './pages/Premium'
import Privacy from './pages/Privacy'
import Settings from './pages/Settings'
import Weight from './pages/Weight'
import { api } from './lib/api'
import { initTelegram, setupBackButton } from './lib/telegram'
import './App.css'

function Splash({ xato, onRetry }) {
  return (
    <div className="splash">
      <div className="splash-logo">🥗</div>
      <div className="splash-name">Luqma AI</div>
      {xato ? (
        <>
          <p className="splash-error">{xato}</p>
          <button className="btn btn-soft splash-retry" onClick={onRetry}>
            Qayta urinish
          </button>
        </>
      ) : (
        <div className="splash-spinner" />
      )}
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [xato, setXato] = useState(null)
  const [sahifa, setSahifa] = useState('home')
  // Yoyiluvchi menyuda tanlangan usul: 'kamera' | 'galereya' | 'matn'
  const [addUsul, setAddUsul] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  // Tanlangan kun App darajasida — yangi ovqat aynan shu kunga saqlanadi.
  const [sana, setSana] = useState(() => new Date())

  const kirish = useCallback(async () => {
    setXato(null)
    try {
      const { user: u } = await api.auth()
      setUser(u)
    } catch (e) {
      setXato(e.message)
    }
  }, [])

  useEffect(() => {
    initTelegram()
    kirish()
  }, [kirish])

  // Bosh sahifadan boshqa joyda Telegram BackButton orqaga qaytaradi.
  useEffect(() => {
    if (sahifa === 'home') return undefined
    return setupBackButton(() => setSahifa('home'))
  }, [sahifa])

  if (!user) return <Splash xato={xato} onRetry={kirish} />

  // Profil to'ldirilmagan bo'lsa avval onboarding.
  if (!user.profil_toliq) {
    return <Onboarding user={user} onDone={setUser} />
  }

  // Chat va vazn to'liq ekranni egallaydi — tab-bar ko'rinmaydi.
  if (sahifa === 'chat') {
    return <Chat onBack={() => setSahifa('home')} />
  }

  if (sahifa === 'mashq') {
    return <Exercise onBack={() => setSahifa('home')} />
  }

  if (sahifa === 'admin') {
    return <Admin onBack={() => setSahifa('settings')} />
  }

  if (sahifa === 'premium') {
    return (
      <Premium
        user={user}
        onUserChange={setUser}
        onBack={() => setSahifa('settings')}
      />
    )
  }

  if (sahifa === 'privacy') {
    return <Privacy onBack={() => setSahifa('settings')} />
  }

  if (sahifa === 'weight') {
    return (
      <Weight
        user={user}
        onUserChange={setUser}
        onBack={() => setSahifa('settings')}
      />
    )
  }

  return (
    <>
      <div className="app">
        {sahifa === 'home' ? (
          <Home
            user={user}
            sana={sana}
            onSanaChange={setSana}
            refreshKey={refreshKey}
            onAdd={(usul) => setAddUsul(usul)}
            onOpenChat={() => setSahifa('chat')}
          />
        ) : (
          <Settings
            user={user}
            onUserChange={setUser}
            onOpenWeight={() => setSahifa('weight')}
            onOpenPrivacy={() => setSahifa('privacy')}
            onOpenAdmin={() => setSahifa('admin')}
            onOpenPremium={() => setSahifa('premium')}
          />
        )}
      </div>

      <TabBar
        active={sahifa}
        onNavigate={setSahifa}
        onAdd={(usul) => setAddUsul(usul)}
        premium={Boolean(user?.premium_faolmi)}
        onPremium={() => setSahifa('premium')}
      />

      <AddMeal
        open={Boolean(addUsul)}
        usul={addUsul}
        sana={sana}
        onClose={() => setAddUsul(null)}
        onSaved={() => setRefreshKey((k) => k + 1)}
      />
    </>
  )
}
