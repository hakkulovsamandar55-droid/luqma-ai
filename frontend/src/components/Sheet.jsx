import { useEffect } from 'react'
import useSheetGesture from '../lib/useSheetGesture'
import { CloseIcon } from './Icons'
import './Sheet.css'

/** Pastdan chiquvchi bottom sheet. */
export default function Sheet({ open, title, onClose, children, footer }) {
  // Ochiq paytda fon skroll qilinmasin.
  useEffect(() => {
    if (!open) return
    const oldingi = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = oldingi
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose?.()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  // Barmoq bilan pastga surib yopish — telefonda o'rganilgan harakat.
  const gesture = useSheetGesture(onClose, { enabled: open })

  if (!open) return null

  return (
    <div className="sheet-root" role="dialog" aria-modal="true" aria-label={title}>
      <div
        className="sheet-backdrop"
        style={gesture.veilStyle}
        onClick={onClose}
      />
      <div className="sheet" ref={gesture.ref} style={gesture.style}>
        <div className="sheet-grip" />
        <header className="sheet-head">
          <h2 className="sheet-title">{title}</h2>
          <button className="sheet-close" onClick={onClose} aria-label="Yopish">
            <CloseIcon size={19} />
          </button>
        </header>
        <div className="sheet-body">{children}</div>
        {footer && <div className="sheet-foot">{footer}</div>}
      </div>
    </div>
  )
}
