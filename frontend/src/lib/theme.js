import { tg } from './telegram'

/**
 * Tema boshqaruvi.
 *
 * Uch holat bor:
 *   'auto'  — Telegram temasiga ergashadi (default)
 *   'dark'  — doim qora
 *   'light' — doim oq
 *
 * Nega default 'auto': foydalanuvchi Telegramni allaqachon o'ziga qulay
 * qilib sozlagan. Kechasi qora Telegramdan oq ilova ochilsa, ko'z og'riydi.
 */
const KALIT = 'luqma-theme'
const TURLAR = ['auto', 'dark', 'light']

export const TEMA_NOMI = {
  auto: 'Avto',
  dark: 'Qora',
  light: 'Oq',
}

/** Saqlangan tanlovni o'qiydi. Xotira ishlamasa 'auto' qaytaradi. */
export function temaniOqi() {
  try {
    const v = localStorage.getItem(KALIT)
    return TURLAR.includes(v) ? v : 'auto'
  } catch {
    return 'auto'
  }
}

/** Telegram qaysi temada ekanini aytadi. Telegramdan tashqarida — tizim. */
function tashqiTema() {
  if (tg?.colorScheme === 'light' || tg?.colorScheme === 'dark') {
    return tg.colorScheme
  }
  try {
    return window.matchMedia('(prefers-color-scheme: light)').matches
      ? 'light'
      : 'dark'
  } catch {
    return 'dark'
  }
}

/** Tanlovni haqiqiy temaga aylantiradi. */
export function haqiqiyTema(tanlov = temaniOqi()) {
  return tanlov === 'auto' ? tashqiTema() : tanlov
}

/** Temani hujjatga qo'llaydi va Telegram panel rangini moslaydi. */
export function temaniQoll(tanlov = temaniOqi()) {
  const tema = haqiqiyTema(tanlov)
  document.documentElement.dataset.theme = tema

  // Telegramning yuqori paneli ham mos rangda bo'lsin — aks holda
  // ilova "yopishtirilgan" ko'rinadi.
  const fon = tema === 'light' ? '#f4f2ee' : '#0a0a0b'
  try {
    tg?.setHeaderColor?.(fon)
    tg?.setBackgroundColor?.(fon)
  } catch {
    /* eski Telegram versiyalarida bu metodlar yo'q */
  }

  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', fon)

  return tema
}

/** Tanlovni saqlaydi va darhol qo'llaydi. */
export function temaniOzgartir(tanlov) {
  try {
    localStorage.setItem(KALIT, tanlov)
  } catch {
    /* xotira ishlamasa ham tema shu sessiyada ishlaydi */
  }
  return temaniQoll(tanlov)
}

/**
 * Tashqi o'zgarishlarni kuzatadi (Telegram temasi yoki tizim sozlamasi).
 * Faqat 'auto' rejimida ta'sir qiladi.
 */
export function temaniKuzat() {
  const yangila = () => {
    if (temaniOqi() === 'auto') temaniQoll('auto')
  }

  tg?.onEvent?.('themeChanged', yangila)

  let mq
  try {
    mq = window.matchMedia('(prefers-color-scheme: light)')
    mq.addEventListener('change', yangila)
  } catch {
    mq = null
  }

  return () => {
    tg?.offEvent?.('themeChanged', yangila)
    mq?.removeEventListener('change', yangila)
  }
}
