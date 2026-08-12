import { PlateIcon, TrashIcon } from './Icons'
import { raqam, vaqtQisqa } from '../lib/format'
import './MealList.css'

/**
 * Ovqatlar — oddiy ro'yxat, oxirgisi yuqorida.
 *
 * Ilgari vaqt bo'yicha guruhlar (Nonushta/Tushlik/...) va har ovqat ostida
 * uchta rangli makro yorlig'i bor edi. Ikkalasi ham olib tashlandi: ro'yxatda
 * odamga kerak bo'lgani — nima yegani, qachon va necha kaloriya. Batafsil
 * ma'lumot ovqat ustiga bosilganda ochiladi.
 */
function MealRow({ meal, onDelete, onOpen }) {
  return (
    <div className="meal">
      <button className="meal-main" onClick={() => onOpen?.(meal)}>
        <span className="meal-thumb">
          {meal.rasm_yoli ? (
            <img src={meal.rasm_yoli} alt="" loading="lazy" />
          ) : (
            <PlateIcon size={20} />
          )}
        </span>

        <span className="meal-info">
          <span className="meal-name">{meal.taom_nomi}</span>
          <span className="meal-time">{vaqtQisqa(meal.vaqt)}</span>
        </span>

        <span className="meal-kcal num">
          {raqam(meal.kaloriya)}
          <i>kcal</i>
        </span>
      </button>

      {onDelete && (
        <button
          className="meal-del"
          onClick={() => onDelete(meal)}
          aria-label={`${meal.taom_nomi} — o'chirish`}
        >
          <TrashIcon size={16} />
        </button>
      )}
    </div>
  )
}

export default function MealList({ meals, onDelete, onOpen }) {
  if (!meals?.length) return null

  const tartib = [...meals].sort((a, b) =>
    String(b.vaqt).localeCompare(String(a.vaqt))
  )

  return (
    <div className="meals">
      {tartib.map((m) => (
        <MealRow key={m.id} meal={m} onDelete={onDelete} onOpen={onOpen} />
      ))}
    </div>
  )
}
