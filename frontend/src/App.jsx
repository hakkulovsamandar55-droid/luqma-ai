import { useCallback, useEffect, useState } from 'react'
import TabBar from './components/TabBar'
import AddMeal from './pages/AddMeal'
import Home from './pages/Home'
import Onboarding from './pages/Onboarding'
import Settings from './pages/Settings'
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
  const [addOchiq, setAddOchiq] = useState(false)
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

  // Sozlamalar sahifasida Telegram BackButton bosh sahifaga qaytaradi.
  useEffect(() => {
    if (sahifa === 'home') return undefined
    return setupBackButton(() => setSahifa('home'))
  }, [sahifa])

  if (!user) return <Splash xato={xato} onRetry={kirish} />

  // Profil to'ldirilmagan bo'lsa avval onboarding.
  if (!user.profil_toliq) {
    return <Onboarding user={user} onDone={setUser} />
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
            onAdd={() => setAddOchiq(true)}
          />
        ) : (
          <Settings user={user} onUserChange={setUser} />
        )}
      </div>

      <TabBar active={sahifa} onNavigate={setSahifa} onAdd={() => setAddOchiq(true)} />

      <AddMeal
        open={addOchiq}
        sana={sana}
        onClose={() => setAddOchiq(false)}
        onSaved={() => setRefreshKey((k) => k + 1)}
      />
    </>
  )
}
