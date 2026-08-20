/** Sana/raqam formatlash yordamchilari (o'zbek tilida). */

export const KUN_QISQA = ['Yak', 'Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan']
export const KUN_TOLIQ = [
  'Yakshanba',
  'Dushanba',
  'Seshanba',
  'Chorshanba',
  'Payshanba',
  'Juma',
  'Shanba',
]
export const OY = [
  'yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun',
  'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr',
]

export const FAOLLIK_NOMLARI = {
  sedentary: 'Harakatsiz',
  light: 'Yengil (1-3 kun)',
  moderate: "O'rtacha (3-5 kun)",
  high: 'Yuqori (6-7 kun)',
  athlete: 'Juda yuqori',
}

export const MAQSAD_NOMLARI = {
  yoqotish: "Vazn yo'qotish",
  saqlash: 'Vaznni saqlash',
  oshirish: 'Vazn oshirish',
}

export const JINS_NOMLARI = { erkak: 'Erkak', ayol: 'Ayol' }

export function sanaSarlavha(date) {
  const bugun = new Date()
  if (birXilKun(date, bugun)) return 'Bugun'

  const kecha = new Date(bugun)
  kecha.setDate(kecha.getDate() - 1)
  if (birXilKun(date, kecha)) return 'Kecha'

  const ertaga = new Date(bugun)
  ertaga.setDate(ertaga.getDate() + 1)
  if (birXilKun(date, ertaga)) return 'Ertaga'

  return `${date.getDate()} ${OY[date.getMonth()]}`
}

export function birXilKun(a, b) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

/** "14:30:00" -> "14:30" */
export function vaqtQisqa(vaqt) {
  return typeof vaqt === 'string' ? vaqt.slice(0, 5) : ''
}

export function raqam(n) {
  const yaxlit = Math.round(n || 0)
  return yaxlit.toLocaleString('ru-RU').replace(/ /g, ' ')
}

/**
 * Millilitrni litrga o'giradi: 1400 -> "1,4".
 *
 * Kichik halqa ichida "1 400" sig'maydi — raqam chetidan chiqib ketadi.
 * Litrda esa qiymat hech qachon uch belgidan oshmaydi.
 */
export function litr(ml) {
  const l = (ml || 0) / 1000
  // Butun bo'lsa keraksiz nol yozilmaydi: 2 -> "2", 1.4 -> "1,4"
  return (Math.round(l * 10) / 10).toLocaleString('ru-RU')
}

/** Manfiy bo'lsa 0 ga, 1 dan oshsa 1 ga qisadi. */
export function nisbat(istemol, limit) {
  if (!limit || limit <= 0) return 0
  return Math.max(0, Math.min(istemol / limit, 1))
}
