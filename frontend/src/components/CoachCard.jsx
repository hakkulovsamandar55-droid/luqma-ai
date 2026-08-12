import './CoachCard.css'

/**
 * Bosh sahifadagi Murabbiy kartochkasi.
 *
 * Ataylab tab-barga to'rtinchi tugma qo'shilmadi — pastki panel uch
 * elementda qolgani sodda. Buning o'rniga kartochka ichida bugungi aniq
 * maslahat ko'rinib turadi, shuning uchun bosishga sabab bor.
 */
export default function CoachCard({ tavsiya, onOpen }) {
  return (
    <button className="coach" onClick={onOpen}>
      <span className="coach-dot" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="17" height="17">
          <path
            d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9 9 0 0 1-3.3-.6L3 21l1.7-5a8.3 8.3 0 0 1-.7-3.4A8.4 8.4 0 0 1 12.5 4 8.4 8.4 0 0 1 21 11.5z"
            fill="none"
            stroke="#fff"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>

      <span className="coach-text">
        <span className="coach-label">
          Murabbiy
          {/* Bu ilovaning asosiy farqi — oddiy kaloriya hisoblagich emas.
              Belgi shuni bir qarashda aytadi. */}
          <i className="coach-badge">AI maslahat</i>
        </span>
        <span className="coach-tip">
          {tavsiya || 'Bugungi ovqatlanishingiz haqida so\u2019rang'}
        </span>
      </span>

      <span className="coach-chev" aria-hidden="true">
        ›
      </span>
    </button>
  )
}
