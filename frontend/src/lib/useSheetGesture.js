import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Pastdan chiqadigan oynani barmoq bilan surib yopish.
 *
 * Nega kerak: telefonda odam oynani pastga surishga urinadi — bu o'rganilgan
 * harakat. Javob bermasa ilova "o'lik" tuyuladi.
 *
 * Muhim jihatlar:
 * - Surish paytida CSS transition o'chiriladi, aks holda barmoq ortidan
 *   kechikib boradi va yopishqoq tuyuladi.
 * - Faqat pastga surishga ruxsat (yuqoriga cho'zilmaydi).
 * - Oyna ichi scroll qilingan bo'lsa surish boshlanmaydi — aks holda
 *   ro'yxatni o'qiyman deb oyna yopilib ketadi.
 * - Yopish qarori masofa VA tezlik bo'yicha: tez qilingan qisqa harakat
 *   ham yopadi (odam shuni kutadi).
 */
const YOPISH_MASOFA = 110
const YOPISH_TEZLIK = 0.5 // px/ms

export default function useSheetGesture(onClose, { enabled = true } = {}) {
  const ref = useRef(null)
  const [siljish, setSiljish] = useState(0)
  const [surilmoqda, setSurilmoqda] = useState(false)

  const holat = useRef({ boshY: 0, boshVaqt: 0, faol: false })

  const boshla = useCallback(
    (e) => {
      if (!enabled) return
      const el = ref.current
      // Ichkarida pastga scroll bo'lgan bo'lsa, avval scroll tugasin.
      if (el && el.scrollTop > 0) return

      holat.current = {
        boshY: e.touches[0].clientY,
        boshVaqt: performance.now(),
        faol: true,
      }
      setSurilmoqda(true)
    },
    [enabled]
  )

  const yur = useCallback((e) => {
    if (!holat.current.faol) return
    const delta = e.touches[0].clientY - holat.current.boshY
    if (delta <= 0) {
      setSiljish(0)
      return
    }
    setSiljish(delta)
  }, [])

  const tugat = useCallback(() => {
    if (!holat.current.faol) return
    holat.current.faol = false
    setSurilmoqda(false)

    const vaqt = performance.now() - holat.current.boshVaqt
    const tezlik = siljish / Math.max(vaqt, 1)

    if (siljish > YOPISH_MASOFA || tezlik > YOPISH_TEZLIK) {
      onClose?.()
      // Yopilgach holatni tozalaymiz — keyingi ochilish toza boshlansin.
      setTimeout(() => setSiljish(0), 250)
    } else {
      setSiljish(0)
    }
  }, [siljish, onClose])

  useEffect(() => {
    const el = ref.current
    if (!el || !enabled) return undefined

    // passive: true — brauzer scroll ni bloklamaydi, sahifa silliq qoladi.
    el.addEventListener('touchstart', boshla, { passive: true })
    el.addEventListener('touchmove', yur, { passive: true })
    el.addEventListener('touchend', tugat)
    el.addEventListener('touchcancel', tugat)

    return () => {
      el.removeEventListener('touchstart', boshla)
      el.removeEventListener('touchmove', yur)
      el.removeEventListener('touchend', tugat)
      el.removeEventListener('touchcancel', tugat)
    }
  }, [boshla, yur, tugat, enabled])

  return {
    ref,
    style: {
      transform: siljish ? `translate3d(0, ${siljish}px, 0)` : undefined,
      transition: surilmoqda ? 'none' : undefined,
    },
    // Fon qorong'uligi surish bilan birga ochiladi — bog'liqlik hissi beradi.
    veilStyle: {
      opacity: siljish ? Math.max(0, 1 - siljish / 320) : undefined,
      transition: surilmoqda ? 'none' : undefined,
    },
    surilmoqda,
  }
}
