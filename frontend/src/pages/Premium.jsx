import { useEffect, useRef, useState } from 'react'
import Sheet from '../components/Sheet'
import { api } from '../lib/api'
import { raqam } from '../lib/format'
import { haptic, showAlert } from '../lib/telegram'
import './Premium.css'

const HOLAT_MATN = {
  kutilmoqda: 'Tekshirilmoqda',
  tasdiqlangan: 'Tasdiqlangan',
  rad_etilgan: 'Rad etilgan',
}

function sana(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`
}

export default function Premium({ user, onBack, onUserChange }) {
  const [tariflar, setTariflar] = useState([])
  const [karta, setKarta] = useState(null)
  const [arizalar, setArizalar] = useState([])
  const [tanlangan, setTanlangan] = useState(null)
  const [yuborilmoqda, setYuborilmoqda] = useState(false)
  const [natija, setNatija] = useState(null)
  const [tolovOchiq, setTolovOchiq] = useState(false)
  const fileRef = useRef(null)

  useEffect(() => {
    Promise.all([
      api.getTariffs().catch(() => []),
      api.getPaymentInfo().catch(() => null),
      api.getMyPayments().catch(() => []),
    ]).then(([t, k, a]) => {
      const royxat = Array.isArray(t) ? t : []
      setTariflar(royxat)
      setKarta(k)
      setArizalar(Array.isArray(a) ? a : [])
      if (royxat.length) setTanlangan(royxat[0])
    })
  }, [])

  function nusxala(matn) {
    navigator.clipboard?.writeText(matn)
    haptic('light')
    showAlert('Nusxalandi')
  }

  async function chekYubor(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !tanlangan) return

    setYuborilmoqda(true)
    setNatija(null)
    haptic('light')

    try {
      const r = await api.sendReceipt(tanlangan.id, file)
      setNatija(r)
      setArizalar((old) => [r, ...old])
      const u = await api.getUser()
      onUserChange?.(u)
    } catch (err) {
      showAlert(err.message)
    } finally {
      setYuborilmoqda(false)
    }
  }

  const premium = user?.premium_faolmi
  const kutilmoqda = user?.premium_tasdiq_kutilmoqda

  const afzalliklar = (karta?.premium_afzalliklar || '')
    .split('\n')
    .map((x) => x.trim())
    .filter(Boolean)

  return (
    <div className="premium">
      <header className="premium-head">
        <button className="premium-back" onClick={onBack} aria-label="Orqaga">
          <svg viewBox="0 0 24 24" width="21" height="21">
            <path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <h1>Premium</h1>
      </header>

      <div className="premium-body">
        {premium && (
          <div className="pstatus">
            <b>Premium faol</b>
            <span>
              {kutilmoqda
                ? "To'lovingiz admin tomonidan tekshirilmoqda. Shu vaqtgacha premium ishlaydi."
                : user?.premium_tugash
                  ? `${sana(user.premium_tugash)} gacha`
                  : 'Muddatsiz'}
            </span>
          </div>
        )}

        {/* Sarlavha va afzalliklar admin paneldan tahrirlanadi. */}
        <h2 className="ptitle">
          {karta?.premium_sarlavha || "Premium bilan ko'proq imkoniyat"}
        </h2>

        {afzalliklar.length > 0 && (
          <ul className="pfeat">
            {afzalliklar.map((a, i) => (
              <li key={i}>
                <span className="pfeat-dot" aria-hidden="true" />
                {a}
              </li>
            ))}
          </ul>
        )}

        {tariflar.length === 0 ? (
          <p className="pbosh">Hozircha tarif yo'q. Keyinroq urinib ko'ring.</p>
        ) : (
          <div className="ptariffs">
            {tariflar.map((t) => (
              <button
                key={t.id}
                className={`ptarif ${tanlangan?.id === t.id ? 'is-on' : ''}`}
                onClick={() => {
                  haptic('light')
                  setTanlangan(t)
                }}
              >
                <span className="ptarif-nom">{t.nom}</span>
                <span className="ptarif-narx num">{raqam(t.narx)} so'm</span>
                {t.tavsif && <span className="ptarif-izoh">{t.tavsif}</span>}
              </button>
            ))}
          </div>
        )}

        {arizalar.length > 0 && (
          <>
            <h2 className="section-title premium-block-head">Arizalaringiz</h2>
            <div className="plist">
              {arizalar.map((a) => (
                <div className="prow" key={a.id}>
                  <div className="prow-main">
                    <b>{a.tarif_nom}</b>
                    <span className="num">
                      {raqam(a.kutilgan_summa)} so'm · {sana(a.created_at)}
                    </span>
                    {a.admin_izoh && <span className="prow-izoh">{a.admin_izoh}</span>}
                  </div>
                  <span className={`ptag ptag-${a.holat}`}>
                    {HOLAT_MATN[a.holat] || a.holat}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Sotib olish tugmasi pastda qotib turadi — u sahifaning maqsadi. */}
      {tanlangan && karta?.karta_raqam && (
        <div className="premium-foot">
          <button
            className="pbtn"
            onClick={() => {
              haptic('light')
              setTolovOchiq(true)
            }}
          >
            Sotib olish · {raqam(tanlangan.narx)} so'm
          </button>
        </div>
      )}

      {/* Ikkinchi bosqich: to'lov va chek. */}
      <Sheet
        open={tolovOchiq}
        title="To'lov"
        onClose={() => setTolovOchiq(false)}
      >
        <p className="pnote pnote-top">
          {tanlangan?.nom} · {raqam(tanlangan?.narx || 0)} so'm
        </p>

        <div className="pcard">
          <button className="pcard-row" onClick={() => nusxala(karta?.karta_raqam)}>
            <span>Karta raqami</span>
            <b className="num">{karta?.karta_raqam}</b>
          </button>
          <div className="pcard-row">
            <span>Karta egasi</span>
            <b>{karta?.karta_egasi}</b>
          </div>
          <button
            className="pcard-row"
            onClick={() => nusxala(String(tanlangan?.narx || ''))}
          >
            <span>Summa</span>
            <b className="num">{raqam(tanlangan?.narx || 0)} so'm</b>
          </button>
        </div>

        {karta?.izoh && <p className="pnote">{karta.izoh}</p>}

        <p className="pnote">
          To'lovdan keyin chek rasmini yuboring. Ma'lumotlar mos kelsa premium
          darhol ishga tushadi, keyin admin qayta tekshiradi.
        </p>

        <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={chekYubor} />
        <button
          className="pbtn"
          disabled={yuborilmoqda}
          onClick={() => fileRef.current?.click()}
        >
          {yuborilmoqda ? 'Tekshirilmoqda…' : 'Chek rasmini tanlash'}
        </button>

        {natija && (
          <div className={`pnatija ${natija.avto_otdi ? 'is-ok' : 'is-wait'}`}>
            <b>{natija.avto_otdi ? 'Premium ishga tushdi' : 'Ariza qabul qilindi'}</b>
            <span>
              {natija.avto_otdi
                ? 'Admin tasdiqlaganidan keyin muddat aniqlanadi.'
                : `Avtomatik tekshiruvdan o'tmadi — admin qo'lda ko'rib chiqadi. ${natija.tekshiruv_izoh || ''}`}
            </span>
          </div>
        )}
      </Sheet>
    </div>
  )
}
