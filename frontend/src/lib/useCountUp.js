import { useEffect, useRef, useState } from 'react'

const reduceMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

/**
 * Raqamni oldingi qiymatdan yangisiga silliq sanab o'tadi.
 * Premium his — raqam sakrab emas, oqib o'zgaradi.
 */
export default function useCountUp(target = 0, duration = 900) {
  const [qiymat, setQiymat] = useState(target)
  const kadr = useRef()
  const boshlangich = useRef(target)

  useEffect(() => {
    if (reduceMotion()) {
      setQiymat(target)
      return undefined
    }

    const from = boshlangich.current
    const delta = target - from
    if (delta === 0) return undefined

    const t0 = performance.now()
    // easeOutCubic — tez boshlanib, oxirida sekinlashadi
    const ease = (t) => 1 - Math.pow(1 - t, 3)

    const yur = (now) => {
      const p = Math.min((now - t0) / duration, 1)
      setQiymat(from + delta * ease(p))
      if (p < 1) kadr.current = requestAnimationFrame(yur)
      else boshlangich.current = target
    }

    kadr.current = requestAnimationFrame(yur)
    return () => cancelAnimationFrame(kadr.current)
  }, [target, duration])

  return qiymat
}
