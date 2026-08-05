import {
  AppleIcon,
  ArrowDownIcon,
  MoonIcon,
  PlateIcon,
  SunIcon,
  SunriseIcon,
  TrashIcon,
} from './Icons'
import { raqam, vaqtQisqa } from '../lib/format'
import './MealList.css'

/**
 * Ovqat vaqti bo'yicha guruhlar — timeline shu tartibda chiziladi.
 * Emoji emas, SVG: emoji shrifti yo'q qurilmalarda ham bir xil ko'rinadi.
 */
const GURUHLAR = [
  { key: 'nonushta', Icon: SunriseIcon, nom: 'Nonushta', gacha: 11 },
  { key: 'tushlik', Icon: SunIcon, nom: 'Tushlik', gacha: 16 },
  { key: 'kechki', Icon: MoonIcon, nom: 'Kechki ovqat', gacha: 22 },
  { key: 'gazak', Icon: AppleIcon, nom: 'Gazak', gacha: 24 },
]

function guruhniTop(vaqt) {
  const soat = Number(String(vaqt || '').slice(0, 2)) || 0
  return GURUHLAR.find((g) => soat < g.gacha) || GURUHLAR[3]
}

function MealCard({ meal, onDelete, onOpen }) {
  return (
    <div className="meal">
      <button className="meal-main" onClick={() => onOpen?.(meal)}>
        <div className="meal-thumb">
          {meal.rasm_yoli ? (
            <img src={meal.rasm_yoli} alt="" loading="lazy" />
          ) : (
            <PlateIcon size={22} />
          )}
        </div>

        <div className="meal-info">
          <div className="meal-name">{meal.taom_nomi}</div>
          <div className="meal-macros">
            <span className="pill pill--protein">{Math.round(meal.protein_g)}g</span>
            <span className="pill pill--carbs">{Math.round(meal.uglevod_g)}g</span>
            <span className="pill pill--fat">{Math.round(meal.yog_g)}g</span>
          </div>
        </div>

        <div className="meal-right">
          <div className="meal-kcal">{raqam(meal.kaloriya)}</div>
          <div className="meal-time">{vaqtQisqa(meal.vaqt)}</div>
        </div>
      </button>

      {onDelete && (
        <button className="meal-del" onClick={() => onDelete(meal)} aria-label="O'chirish">
          <TrashIcon size={17} />
        </button>
      )}
    </div>
  )
}

/** Bo'sh holat — pastdagi '+' tugmaga ishora qiluvchi strelka bilan. */
function EmptyState() {
  return (
    <div className="meal-empty fade-up">
      <div className="meal-empty-art">
        <PlateIcon size={38} />
      </div>
      <div className="meal-empty-title">Hozircha ma'lumot yo'q</div>
      <p className="meal-empty-text">
        Ovqatingizni suratga oling — Luqma AI uni tanib, kaloriya va BJU sini
        hisoblab beradi.
      </p>
      <div className="meal-empty-arrow" aria-hidden="true">
        <ArrowDownIcon size={26} />
      </div>
    </div>
  )
}

export default function MealList({ meals, onDelete, onOpen }) {
  if (!meals?.length) return <EmptyState />

  // Vaqt bo'yicha guruhlaymiz, har guruh ichida ertalabdan kechga qarab.
  const guruhlangan = GURUHLAR.map((g) => ({
    ...g,
    ovqatlar: meals
      .filter((m) => guruhniTop(m.vaqt).key === g.key)
      .sort((a, b) => String(a.vaqt).localeCompare(String(b.vaqt))),
  })).filter((g) => g.ovqatlar.length > 0)

  let indeks = 0

  return (
    <div className="timeline">
      {guruhlangan.map((g) => {
        const jami = g.ovqatlar.reduce((s, m) => s + m.kaloriya, 0)
        return (
          <section className="tl-group" key={g.key}>
            <header className="tl-head">
              <span className={`tl-dot tl-dot--${g.key}`} aria-hidden="true">
                <g.Icon size={13} />
              </span>
              <span className="tl-name">{g.nom}</span>
              <span className="tl-kcal">{raqam(jami)} kcal</span>
            </header>

            <div className="tl-items">
              {g.ovqatlar.map((m) => {
                indeks += 1
                return (
                  <div
                    className="tl-item fade-up"
                    key={m.id}
                    style={{ animationDelay: `${Math.min(indeks * 55, 400)}ms` }}
                  >
                    <MealCard meal={m} onDelete={onDelete} onOpen={onOpen} />
                  </div>
                )
              })}
            </div>
          </section>
        )
      })}
    </div>
  )
}
