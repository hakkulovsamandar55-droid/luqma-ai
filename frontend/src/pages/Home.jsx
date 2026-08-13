import { useCallback, useEffect, useState } from 'react'
import CoachCard from '../components/CoachCard'
import Logo from '../components/Logo'
import DayStrip from '../components/DayStrip'
import MacroCards from '../components/MacroCards'
import MealList from '../components/MealList'
import MealSheet from '../components/MealSheet'
import Sheet from '../components/Sheet'
import ProgressRing from '../components/ProgressRing'
import WeeklyChart from '../components/WeeklyChart'
import { api, toApiDate } from '../lib/api'
import { birXilKun, raqam } from '../lib/format'
import { haptic, showConfirm } from '../lib/telegram'
import './Home.css'

export default function Home({
  user,
  sana,
  onSanaChange,
  onAdd,
  onOpenChat,
  refreshKey,
}) {
  const [summary, setSummary] = useState(null)
  const [meals, setMeals] = useState([])
  const [weekly, setWeekly] = useState(null)
  const [tavsiya, setTavsiya] = useState(null)
  const [statsOchiq, setStatsOchiq] = useState(false)
  const [royxatOchiq, setRoyxatOchiq] = useState(false)
  const [tanlangan, setTanlangan] = useState(null)
  const [yuklanmoqda, setYuklanmoqda] = useState(true)
  const [xato, setXato] = useState(null)

  const apiSana = toApiDate(sana)
  const bugunmi = birXilKun(sana, new Date())

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

  useEffect(() => {
    if (!bugunmi) return setTavsiya(null)
    api
      .getCoachTip()
      .then((r) => setTavsiya(r?.tavsiya || null))
      .catch(() => setTavsiya(null))
  }, [bugunmi, refreshKey])

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
    setSummary((s) => (s ? { ...s, suv_ml: Math.max(0, s.suv_ml + delta) } : s))
    try {
      const r = await api.addWater(delta, apiSana)
      setSummary((s) => (s ? { ...s, suv_ml: r.miqdor_ml } : s))
    } catch {
      yukla()
    }
  }

  return (
    <div className="home">
      {/* Gradientning to'q zonasi: nom, kunlar va halqa */}
      <header className="home-head">
        <Logo size="md" />
      </header>

      <DayStrip selected={sana} onSelect={onSanaChange} />

      {xato && (
        <div className="home-error">
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

        {bugunmi && <CoachCard tavsiya={tavsiya} onOpen={onOpenChat} />}

        <div className="home-meals">
          <div className="home-meals-head">
            <h2>Yaqinda iste'mol qilindi</h2>
            {meals.length > 0 && (
              <button
                className="home-more"
                onClick={() => {
                  haptic('light')
                  setRoyxatOchiq(true)
                }}
              >
                Batafsil
              </button>
            )}
          </div>

          {meals.length === 0 ? (
            /* Bo'sh holat — namunadagidek oq kartochka va pastga
               ishora qiluvchi qo'lda chizilgan strelka. */
            <div className="home-empty">
              <b>Hozircha ma'lumot yo'q!</b>
              <p>Bugungi ovqatlaringizni tez suratga olib kuzatishni boshlang</p>
              <svg
                className="home-empty-arrow"
                width="52"
                height="60"
                viewBox="0 0 52 60"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M17 3c9 6 10 14 4 17-5 2.6-8-1.4-5.6-5.4C18.4 10 27 9 30 18c2.6 7.8-1 17-6 28" />
                <path d="M31 40c-2 3.4-4.4 7.6-7 11M14 42c3.6 2.6 7.2 5.6 10 9" />
              </svg>
            </div>
          ) : (
            <MealList
              meals={meals}
              onDelete={ovqatniOchir}
              onOpen={setTanlangan}
            />
          )}
        </div>
      </div>

      <Sheet
        open={royxatOchiq}
        title="Suv va statistika"
        onClose={() => setRoyxatOchiq(false)}
      >
        <div className="home-water">
          <div className="home-water-txt">
            <b>Suv</b>
            <span className="num">
              {raqam(summary?.suv_ml || 0)} / {raqam(summary?.suv_limit_ml || 2000)} ml
            </span>
          </div>
          <button className="home-water-btn" onClick={() => suvOzgartir(-250)}>
            −
          </button>
          <button
            className="home-water-btn is-primary"
            onClick={() => suvOzgartir(250)}
          >
            +
          </button>
        </div>

        <button
          className="stats-toggle"
          onClick={() => {
            haptic('light')
            setStatsOchiq((v) => !v)
          }}
        >
          {statsOchiq ? 'Statistikani yashirish' : 'Haftalik statistika'}
        </button>

        {statsOchiq && weekly && <WeeklyChart data={weekly} />}
      </Sheet>

      <MealSheet
        meal={tanlangan}
        onClose={() => setTanlangan(null)}
        onSaved={yukla}
        onDelete={ovqatniOchir}
      />
    </div>
  )
}
