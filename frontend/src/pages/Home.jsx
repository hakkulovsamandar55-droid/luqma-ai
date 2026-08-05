import { useCallback, useEffect, useState } from 'react'
import DayStrip from '../components/DayStrip'
import MacroCards from '../components/MacroCards'
import MealList from '../components/MealList'
import ProgressRing from '../components/ProgressRing'
import WaterCard from '../components/WaterCard'
import WeeklyChart from '../components/WeeklyChart'
import { ChartIcon, FireIcon, SparkIcon } from '../components/Icons'
import { api, toApiDate } from '../lib/api'
import { birXilKun, sanaSarlavha } from '../lib/format'
import { haptic, showConfirm } from '../lib/telegram'
import './Home.css'

export default function Home({ user, sana, onSanaChange, onAdd, onOpenMeal, refreshKey }) {
  const [summary, setSummary] = useState(null)
  const [meals, setMeals] = useState([])
  const [weekly, setWeekly] = useState(null)
  const [statsOchiq, setStatsOchiq] = useState(false)
  const [yuklanmoqda, setYuklanmoqda] = useState(true)
  const [xato, setXato] = useState(null)

  const apiSana = toApiDate(sana)

  const yukla = useCallback(async () => {
    setXato(null)
    try {
      const [s, m] = await Promise.all([api.getSummary(apiSana), api.getMeals(apiSana)])
      setSummary(s)
      setMeals(m)
    } catch (e) {
      setXato(e.message)
    } finally {
      setYuklanmoqda(false)
    }
  }, [apiSana])

  useEffect(() => {
    setYuklanmoqda(true)
    yukla()
  }, [yukla, refreshKey])

  // Haftalik grafik faqat ochilganda yuklanadi.
  useEffect(() => {
    if (!statsOchiq) return
    api.getWeekly(apiSana).then(setWeekly).catch(() => {})
  }, [statsOchiq, apiSana, refreshKey])

  async function ovqatniOchir(meal) {
    if (!(await showConfirm(`"${meal.taom_nomi}" o'chirilsinmi?`))) return
    haptic('warning')
    setMeals((oldingi) => oldingi.filter((m) => m.id !== meal.id))
    try {
      await api.deleteMeal(meal.id)
    } finally {
      yukla()
    }
  }

  async function suvOzgartir(delta) {
    // Optimistik yangilash — tugma darhol javob bersin.
    setSummary((s) => (s ? { ...s, suv_ml: Math.max(0, s.suv_ml + delta) } : s))
    try {
      const r = await api.addWater(delta, apiSana)
      setSummary((s) => (s ? { ...s, suv_ml: r.miqdor_ml } : s))
    } catch {
      yukla()
    }
  }

  const bugunmi = birXilKun(sana, new Date())
  const streak = summary?.streak || 0

  return (
    <div className="home">
      <header className="home-head">
        <h1 className="page-title">Luqma AI</h1>
        {streak > 1 && (
          <div className="streak" title="Ketma-ket kunlar">
            <FireIcon size={15} />
            {streak}
          </div>
        )}
      </header>

      <DayStrip selected={sana} onSelect={onSanaChange} />

      {xato && (
        <div className="home-error card">
          <span>{xato}</span>
          <button className="btn btn-ghost" onClick={yukla}>
            Qayta urinish
          </button>
        </div>
      )}

      <div className={`home-body ${yuklanmoqda ? 'is-loading' : ''}`}>
        <ProgressRing
          istemol={summary?.kaloriya?.istemol || 0}
          limit={summary?.kaloriya?.limit || user?.kunlik_kaloriya_limit || 2000}
        />

        <MacroCards summary={summary} />

        {/* Ovqatlar ro'yxati — asosiy kontent, shuning uchun ekranning yuqori
            qismida turadi. Suv va statistika ikkilamchi, pastda. */}
        <div className="home-list-head">
          <h2 className="section-title">
            {bugunmi ? "Bugun iste'mol qilindi" : `${sanaSarlavha(sana)} — ovqatlar`}
          </h2>
          {meals.length > 0 && (
            <span className="home-list-count">{meals.length} ta</span>
          )}
        </div>

        <MealList meals={meals} onDelete={ovqatniOchir} onOpen={onOpenMeal} />

        {meals.length === 0 && !yuklanmoqda && bugunmi && (
          <button className="suggest-btn" onClick={onAdd}>
            <SparkIcon size={17} />
            Birinchi ovqatni qo'shish
          </button>
        )}

        <WaterCard
          suvMl={summary?.suv_ml || 0}
          limitMl={summary?.suv_limit_ml || user?.kunlik_suv_limit_ml || 2000}
          onChange={suvOzgartir}
          disabled={yuklanmoqda}
        />

        <button
          className="stats-toggle"
          onClick={() => {
            haptic('light')
            setStatsOchiq((v) => !v)
          }}
        >
          <ChartIcon size={17} />
          {statsOchiq ? 'Statistikani yashirish' : 'Haftalik statistika'}
        </button>

        {statsOchiq && weekly && <WeeklyChart data={weekly} />}
      </div>
    </div>
  )
}
