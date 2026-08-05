/**
 * Telegram Web App SDK ustidan yupqa qatlam.
 * Brauzerda (SDK yo'q paytda) ham ilova ishlashi uchun barcha chaqiruvlar xavfsiz.
 */

export const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : undefined

export const isTelegram = Boolean(tg?.initData)

export function initTelegram() {
  if (!tg) return
  tg.ready()
  tg.expand()
  // Telegram 7.7+ — pastga tortib yopilishni oldini oladi (skroll bilan chalkashmasin)
  tg.disableVerticalSwipes?.()
  tg.setHeaderColor?.('#F4F4F7')
  tg.setBackgroundColor?.('#F4F4F7')
}

export function getInitData() {
  return tg?.initData || ''
}

/** Tebranishli fikr-mulohaza (haptic feedback). */
export function haptic(type = 'light') {
  const h = tg?.HapticFeedback
  if (!h) return
  if (type === 'success' || type === 'error' || type === 'warning') {
    h.notificationOccurred?.(type)
  } else if (type === 'select') {
    h.selectionChanged?.()
  } else {
    h.impactOccurred?.(type)
  }
}

/** Telegram BackButton ni ko'rsatadi. Tozalash funksiyasini qaytaradi. */
export function setupBackButton(onBack) {
  const bb = tg?.BackButton
  if (!bb) return () => {}
  bb.onClick(onBack)
  bb.show()
  return () => {
    bb.offClick(onBack)
    bb.hide()
  }
}

export function showAlert(message) {
  if (tg?.showAlert) tg.showAlert(message)
  else window.alert(message)
}

export function showConfirm(message) {
  return new Promise((resolve) => {
    if (tg?.showConfirm) tg.showConfirm(message, resolve)
    else resolve(window.confirm(message))
  })
}
