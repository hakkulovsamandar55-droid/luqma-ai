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
import { birXilKun, raqam, sanaSarlavha } from '../lib/format'
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
  // Bosilgan ovqat — tahrirlash oynasida ochiladi.
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

  // Murabbiyning bir qatorlik maslahati — kartochka ichida ko'rinadi.
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
      {/* Sozlamalar pastki panelda — bu yerda takrorlanmaydi. */}
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

      {/* Ekran skroll qilinmaydi: hamma narsa bir ko'rinishda turadi.
          Ovqatlar ro'yxati va haftalik statistika pastdan chiquvchi
          oynaga ko'chirildi — ular kerak bo'lganda ochiladi. */}
      <div className={`home-body ${yuklanmoqda ? 'is-loading' : ''}`}>
        {/* O'lcham kichikroq: ekranga sig'ishi kerak, skroll yo'q. */}
        <ProgressRing
          istemol={summary?.kaloriya?.istemol || 0}
          limit={summary?.kaloriya?.limit || user?.kunlik_kaloriya_limit || 2000}
        />

        <MacroCards
          summary={summary}
          suvMl={summary?.suv_ml || 0}
          suvLimit={summary?.suv_limit_ml || user?.kunlik_suv_limit_ml || 2000}
        />

        {bugunmi && <CoachCard tavsiya={tavsiya} onOpen={onOpenChat} />}

        {/* Ovqatlar ro'yxati ekranning o'zida turadi — foydalanuvchi
            uni ko'rish uchun hech narsa bosmaydi. Faqat ro'yxatning
            o'zi skroll qilinadi, sahifa emas. */}
        <div className="home-meals">
          <div className="home-meals-head">
            <span>
              {meals.length > 0
                ? `Bugun ${meals.length} ta ovqat`
                : 'Bugungi ovqatlar'}
            </span>
            <button
              className="home-more"
              onClick={() => {
                haptic('light')
                setRoyxatOchiq(true)
              }}
            >
              Batafsil
            </button>
          </div>

          <div className="home-meals-scroll">
            {meals.length === 0 ? (
              <p className="home-empty-txt">Hali hech narsa qo'shilmagan</p>
            ) : (
              <MealList
                meals={meals}
                onDelete={ovqatniOchir}
                onOpen={setTanlangan}
              />
            )}
          </div>
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
