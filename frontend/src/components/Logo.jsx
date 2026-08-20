import './Logo.css'

/**
 * Ilova nomi. Ilgari "Luqma • AI" ko'rinishida, o'rtasida lime nuqta
 * bilan yozilardi. Namuna dizaynda nom oddiy va yengil — bezaksiz.
 */
export default function Logo({ size = 'md' }) {
  return <span className={`logo logo-${size}`}>Luqma AI</span>
}
