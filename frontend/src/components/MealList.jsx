import { ArrowDownIcon, PlateIcon, TrashIcon } from './Icons'
import { raqam, vaqtQisqa } from '../lib/format'
import './MealList.css'

/** Bitta ovqat kartochkasi. */
function MealCard({ meal, onDelete, onOpen }) {
  return (
    <div className="meal fade-up">
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
            <span className="dot dot--protein" />
            {Math.round(meal.protein_g)}g
            <span className="dot dot--carbs" />
            {Math.round(meal.uglevod_g)}g
            <span className="dot dot--fat" />
            {Math.round(meal.yog_g)}g
          </div>
        </div>

        <div className="meal-right">
          <div className="meal-kcal">{raqam(meal.kaloriya)}</div>
          <div className="meal-time">{vaqtQisqa(meal.vaqt)}</div>
        </div>
      </button>

      {onDelete && (
        <button
          className="meal-del"
          onClick={() => onDelete(meal)}
          aria-label="O'chirish"
        >
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

  return (
    <div className="meal-list">
      {meals.map((m) => (
        <MealCard key={m.id} meal={m} onDelete={onDelete} onOpen={onOpen} />
      ))}
    </div>
  )
}
