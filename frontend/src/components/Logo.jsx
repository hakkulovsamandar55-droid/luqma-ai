import './Logo.css'

/**
 * Ilova nomi. Qo'lyozma logotip olib tashlandi — interfeysda oddiy,
 * o'qiladigan matn turadi. Brend belgisi (lime nuqta) qoldi: u eng
 * kichik tanilish elementi va bezakka aylanmaydi.
 */
export default function Logo({ size = 'md' }) {
  return (
    <span className={`logo logo-${size}`} aria-label="Luqma AI">
      Luqma
      <span className="logo-dot" aria-hidden="true" />
      AI
    </span>
  )
}
