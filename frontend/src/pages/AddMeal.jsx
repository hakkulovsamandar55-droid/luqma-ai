import { useEffect, useRef, useState } from 'react'
import Sheet from '../components/Sheet'
import {
  CameraIcon,
  CheckIcon,
  CloseIcon,
  GalleryIcon,
  PencilIcon,
  SparkIcon,
  StarIcon,
} from '../components/Icons'
import { api, toApiDate } from '../lib/api'
import { haptic, showAlert } from '../lib/telegram'
import './AddMeal.css'

const BOSQICH = {
  TANLASH: 'tanlash',
  MATN: 'matn',
  QIDIRUV: 'qidiruv',
  YUKLASH: 'yuklash',
  NATIJA: 'natija',
}

/** AI tahlil qilayotgan paytdagi holat. */
function Loading({ rasmUrl }) {
  return (
    <div className="analyzing">
      {rasmUrl ? (
        <div className="analyzing-photo">
          <img src={rasmUrl} alt="" />
          <div className="analyzing-scan" />
        </div>
      ) : (
        <div className="analyzing-spinner" />
      )}
      <div className="analyzing-title">
        <SparkIcon size={17} />
        AI tahlil qilmoqda...
      </div>
      <p className="analyzing-text">
        Taom aniqlanmoqda va ozuqaviy qiymati hisoblanmoqda. Bu bir necha soniya
        oladi.
      </p>
    </div>
  )
}

/**
 * Makrolarning kaloriyadagi ulushi — bitta yig'ma chiziq.
 * Raqamlar pastda baribir tahrirlanadi, bu faqat vizual xulosa.
 */
function MacroSplit({ natija }) {
  const p = (Number(natija.protein_g) || 0) * 4
  const u = (Number(natija.uglevod_g) || 0) * 4
  const y = (Number(natija.yog_g) || 0) * 9
  const jami = p + u + y
  if (jami <= 0) return null

  const qismlar = [
    { tur: 'protein', nom: 'Oqsil', ulush: (p / jami) * 100 },
    { tur: 'carbs', nom: 'Uglevod', ulush: (u / jami) * 100 },
    { tur: 'fat', nom: "Yog'", ulush: (y / jami) * 100 },
  ]

  return (
    <div className="split">
      <div className="split-bar">
        {qismlar.map((q) => (
          <span key={q.tur} className={`split-${q.tur}`} style={{ width: `${q.ulush}%` }} />
        ))}
      </div>
      <div className="split-legend">
        {qismlar.map((q) => (
          <span key={q.tur} className="split-item">
            <i className={`split-dot split-${q.tur}`} />
            {q.nom} <b>{Math.round(q.ulush)}%</b>
          </span>
        ))}
      </div>
    </div>
  )
}

/** Tahrirlanadigan raqamli maydon. */
function NumField({ label, value, onChange, unit, tur }) {
  return (
    <label className={`nf ${tur ? `nf--${tur}` : ''}`}>
      <span className="nf-label">{label}</span>
      <span className="nf-input">
        <input
          type="number"
          inputMode="decimal"
          min="0"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={(e) => e.target.select()}
        />
        <span className="nf-unit">{unit}</span>
      </span>
    </label>
  )
}

export default function AddMeal({ open, usul, onClose, onSaved, sana }) {
  const [bosqich, setBosqich] = useState(BOSQICH.TANLASH)
  const [natija, setNatija] = useState(null)
  const [qidiruv, setQidiruv] = useState('')
  const [topilgan, setTopilgan] = useState([])
  const [qidirilmoqda, setQidirilmoqda] = useState(false)
  const [rasmUrl, setRasmUrl] = useState(null)
  const [matn, setMatn] = useState('')
  const [saqlanmoqda, setSaqlanmoqda] = useState(false)
  const [saqlandi, setSaqlandi] = useState(false)
  const [favorites, setFavorites] = useState([])
  const [favSifatidaSaqla, setFavSifatidaSaqla] = useState(false)

  const cameraRef = useRef(null)
  const galleryRef = useRef(null)

  // Har ochilganda toza holatdan boshlaymiz.
  useEffect(() => {
    if (!open) return
    setBosqich(BOSQICH.TANLASH)
    setNatija(null)
    setMatn('')
    setFavSifatidaSaqla(false)
    setSaqlanmoqda(false)
    setSaqlandi(false)
    setRasmUrl((oldingi) => {
      if (oldingi) URL.revokeObjectURL(oldingi)
      return null
    })
    api
      .getFavorites()
      .then((r) => setFavorites(Array.isArray(r) ? r : []))
      .catch(() => {})
  }, [open])

  // Pastki paneldagi yoyiluvchi menyu usulni allaqachon tanlagan —
  // tanlash bosqichini takrorlamaymiz va to'g'ridan-to'g'ri o'tamiz.
  useEffect(() => {
    if (!open || !usul) return
    if (usul === 'matn') {
      setBosqich(BOSQICH.MATN)
    } else if (usul === 'qidiruv') {
      setBosqich(BOSQICH.QIDIRUV)
    } else if (usul === 'kamera') {
      cameraRef.current?.click()
    } else if (usul === 'galereya') {
      galleryRef.current?.click()
    }
  }, [open, usul])

  // Sheet yopilganda blob URL ni bo'shatamiz.
  useEffect(() => () => rasmUrl && URL.revokeObjectURL(rasmUrl), [rasmUrl])

  async function rasmniTahlilQil(file) {
    if (!file) return
    const oldindanKorish = URL.createObjectURL(file)
    setRasmUrl(oldindanKorish)
    setBosqich(BOSQICH.YUKLASH)
    haptic('light')

    try {
      const r = await api.analyzeImage(file)
      setNatija(r)
      setBosqich(BOSQICH.NATIJA)
      haptic('success')
    } catch (e) {
      haptic('error')
      showAlert(e.message)
      setBosqich(BOSQICH.TANLASH)
    }
  }

  async function matnniTahlilQil() {
    const qiymat = matn.trim()
    if (qiymat.length < 2) return
    setBosqich(BOSQICH.YUKLASH)
    try {
      const r = await api.analyzeText(qiymat)
      setNatija(r)
      setBosqich(BOSQICH.NATIJA)
      haptic('success')
    } catch (e) {
      haptic('error')
      showAlert(e.message)
      setBosqich(BOSQICH.MATN)
    }
  }

  // Bazadan qidirish — AI chaqirilmaydi, shuning uchun tez va bepul.
  useEffect(() => {
    if (bosqich !== BOSQICH.QIDIRUV) return undefined

    setQidirilmoqda(true)
    const t = setTimeout(() => {
      api
        .searchFoods(qidiruv)
        .then((r) => setTopilgan(Array.isArray(r) ? r : []))
        .catch(() => setTopilgan([]))
        .finally(() => setQidirilmoqda(false))
    }, qidiruv ? 280 : 0)

    return () => clearTimeout(t)
  }, [bosqich, qidiruv])

  function bazadanQosh(f) {
    haptic('light')
    setNatija({
      taom_nomi: f.nom,
      ulush: f.ulush,
      kaloriya: f.kaloriya,
      protein_g: f.protein_g,
      yog_g: f.yog_g,
      uglevod_g: f.uglevod_g,
      rasm_yoli: null,
      manba: 'database',
    })
    setBosqich(BOSQICH.NATIJA)
  }

  function favoritdanQosh(fav) {
    haptic('light')
    setNatija({
      taom_nomi: fav.taom_nomi,
      ulush: fav.ulush,
      kaloriya: fav.kaloriya,
      protein_g: fav.protein_g,
      yog_g: fav.yog_g,
      uglevod_g: fav.uglevod_g,
      rasm_yoli: null,
      manba: 'favorite',
    })
    setBosqich(BOSQICH.NATIJA)
  }

  async function saqla() {
    if (!natija?.taom_nomi?.trim()) {
      showAlert('Taom nomini kiriting')
      return
    }
    setSaqlanmoqda(true)
    const payload = {
      taom_nomi: natija.taom_nomi.trim(),
      ulush: natija.ulush || null,
      kaloriya: Math.round(Number(natija.kaloriya) || 0),
      protein_g: Number(natija.protein_g) || 0,
      yog_g: Number(natija.yog_g) || 0,
      uglevod_g: Number(natija.uglevod_g) || 0,
      rasm_yoli: natija.rasm_yoli || null,
      manba: natija.manba || 'ai',
      sana: sana ? toApiDate(sana) : undefined,
    }

    try {
      await api.createMeal(payload)
      if (favSifatidaSaqla) {
        await api.addFavorite({
          taom_nomi: payload.taom_nomi,
          ulush: payload.ulush,
          kaloriya: payload.kaloriya,
          protein_g: payload.protein_g,
          yog_g: payload.yog_g,
          uglevod_g: payload.uglevod_g,
        })
      }
      haptic('success')
      onSaved()
      // Yopishdan oldin qisqa tasdiq animatsiyasi ko'rsatiladi.
      setSaqlandi(true)
      setTimeout(() => {
        setSaqlandi(false)
        onClose()
      }, 1050)
    } catch (e) {
      haptic('error')
      showAlert(e.message)
      setSaqlanmoqda(false)
    }
  }

  const sarlavha = {
    [BOSQICH.TANLASH]: "Ovqat qo'shish",
    [BOSQICH.MATN]: 'Qo\'lda kiritish',
    [BOSQICH.QIDIRUV]: 'Ovqat qidirish',
    [BOSQICH.YUKLASH]: 'Tahlil qilinmoqda',
    [BOSQICH.NATIJA]: 'Natijani tekshiring',
  }[bosqich]

  const footer =
    bosqich === BOSQICH.NATIJA ? (
      <button className="btn btn-primary" onClick={saqla} disabled={saqlanmoqda}>
        {saqlanmoqda ? (
          'Saqlanmoqda...'
        ) : (
          <>
            <CheckIcon size={19} /> Saqlash
          </>
        )}
      </button>
    ) : bosqich === BOSQICH.QIDIRUV ? (
      <div className="search">
        {/* Tozalash tugmasi o'zimizniki. Brauzerning ichki
            (-webkit-search-cancel-button) tugmasi Chrome da KO'K "✕" bo'lib
            chiqadi va ilova palitrasiga umuman mos kelmaydi — u CSS da
            o'chirilgan. */}
        <div className="search-box">
          <input
            className="search-input"
            type="search"
            autoFocus
            placeholder="Masalan: osh, somsa, tuxum"
            value={qidiruv}
            onChange={(e) => setQidiruv(e.target.value)}
          />
          {qidiruv && (
            <button
              className="search-clear"
              onClick={() => setQidiruv('')}
              aria-label="Tozalash"
            >
              <CloseIcon size={15} />
            </button>
          )}
        </div>

        {qidirilmoqda && topilgan.length === 0 ? (
          <p className="search-bosh">Qidirilmoqda…</p>
        ) : topilgan.length === 0 ? (
          <div className="search-bosh">
            <p>Bazadan topilmadi.</p>
            <button
              className="btn btn-soft"
              onClick={() => setBosqich(BOSQICH.MATN)}
            >
              AI bilan tahlil qilish
            </button>
          </div>
        ) : (
          <div className="search-list">
            {topilgan.map((f) => (
              <button key={f.id} className="search-row" onClick={() => bazadanQosh(f)}>
                <span className="search-txt">
                  <b>{f.nom}</b>
                  <span>{f.ulush}</span>
                </span>
                <span className="search-kcal num">
                  {f.kaloriya}
                  <i>kcal</i>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    ) : bosqich === BOSQICH.MATN ? (
      <button
        className="btn btn-primary"
        onClick={matnniTahlilQil}
        disabled={matn.trim().length < 2}
      >
        <SparkIcon size={18} /> Tahlil qilish
      </button>
    ) : null

  // Saqlangandan keyingi tasdiq — belgi chizilib chiqadi.
  if (open && saqlandi) {
    return (
      <Sheet open title="Saqlandi" onClose={() => {}}>
        <div className="saved">
          <svg className="saved-mark" viewBox="0 0 52 52" aria-hidden="true">
            <circle className="saved-ring" cx="26" cy="26" r="23" />
            <path className="saved-tick" d="M15 27.5 22.5 35 38 19" />
          </svg>
          <div className="saved-title">Ovqat qo'shildi</div>
          <p className="saved-text">Kunlik hisobingiz yangilandi</p>
        </div>
      </Sheet>
    )
  }

  return (
    <Sheet open={open} title={sarlavha} onClose={onClose} footer={footer}>
      {/* --- 1-bosqich: manbani tanlash --- */}
      {bosqich === BOSQICH.TANLASH && (
        <div className="add-options">
          <button className="opt" onClick={() => cameraRef.current?.click()}>
            <span className="opt-icon opt-icon--accent">
              <CameraIcon size={22} />
            </span>
            <span className="opt-text">
              <b>Rasmga olish</b>
              <small>Kamerani ochib, ovqatni suratga oling</small>
            </span>
          </button>

          <button className="opt" onClick={() => galleryRef.current?.click()}>
            <span className="opt-icon">
              <GalleryIcon size={22} />
            </span>
            <span className="opt-text">
              <b>Galereyadan tanlash</b>
              <small>Tayyor rasmni yuklang</small>
            </span>
          </button>

          <button className="opt" onClick={() => setBosqich(BOSQICH.MATN)}>
            <span className="opt-icon">
              <PencilIcon size={22} />
            </span>
            <span className="opt-text">
              <b>Qo'lda kiritish</b>
              <small>Masalan: "150g osh"</small>
            </span>
          </button>

          {favorites.length > 0 && (
            <>
              <div className="section-title">Sevimli taomlar</div>
              <div className="favs">
                {favorites.map((f) => (
                  <button key={f.id} className="fav" onClick={() => favoritdanQosh(f)}>
                    <StarIcon size={14} />
                    <span className="fav-name">{f.taom_nomi}</span>
                    <span className="fav-kcal">{f.kaloriya}</span>
                  </button>
                ))}
              </div>
            </>
          )}

          {/* capture="environment" — mobil qurilmada to'g'ridan-to'g'ri kamerani ochadi */}
          <input
            ref={cameraRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            hidden
            onChange={(e) => rasmniTahlilQil(e.target.files?.[0])}
          />
          <input
            ref={galleryRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={(e) => rasmniTahlilQil(e.target.files?.[0])}
          />
        </div>
      )}

      {/* --- Qo'lda kiritish --- */}
      {bosqich === BOSQICH.MATN && (
        <div className="add-manual">
          <label className="tf">
            <span className="tf-label">Nima yedingiz?</span>
            <input
              type="text"
              autoFocus
              placeholder="Masalan: 1 kosa lag'mon va 2 dona non"
              value={matn}
              onChange={(e) => setMatn(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && matnniTahlilQil()}
            />
          </label>
          <p className="hint">
            Miqdorni ham yozing (gramm, kosa, dona) — shunda hisob aniqroq bo'ladi.
          </p>
        </div>
      )}

      {/* --- Yuklanmoqda --- */}
      {bosqich === BOSQICH.YUKLASH && <Loading rasmUrl={rasmUrl} />}

      {/* --- Natija (tahrirlanadigan) --- */}
      {bosqich === BOSQICH.NATIJA && natija && (
        <div className="result fade-up">
          {rasmUrl && (
            <div className="result-photo">
              <img src={rasmUrl} alt="" />
              {natija.ishonch > 0 && (
                <span className="ai-badge">
                  <StarIcon size={12} />
                  AI {Math.round(natija.ishonch * 100)}% ishonch
                </span>
              )}
            </div>
          )}

          <label className="tf">
            <span className="tf-label">Taom nomi</span>
            <input
              type="text"
              value={natija.taom_nomi}
              onChange={(e) => setNatija({ ...natija, taom_nomi: e.target.value })}
            />
          </label>

          {natija.ulush && <div className="result-portion">{natija.ulush}</div>}

          {/* AI tavsiyasi — suhbat pufakchasi ko'rinishida */}
          {natija.izoh && (
            <div className="ai-bubble">
              <span className="ai-avatar">
                <SparkIcon size={15} />
              </span>
              <div className="ai-body">
                <b>Luqma AI tavsiya qiladi</b>
                <p>{natija.izoh}</p>
              </div>
            </div>
          )}

          {natija.ishonch > 0 && natija.ishonch < 0.6 && (
            <div className="result-warn">
              AI bu taomga to'liq ishonchi komil emas — raqamlarni tekshirib chiqing.
            </div>
          )}

          <MacroSplit natija={natija} />

          <NumField
            label="Kaloriya"
            unit="kcal"
            value={natija.kaloriya}
            onChange={(v) => setNatija({ ...natija, kaloriya: v })}
          />

          <div className="result-macros">
            <NumField
              label="Oqsil"
              unit="g"
              tur="protein"
              value={natija.protein_g}
              onChange={(v) => setNatija({ ...natija, protein_g: v })}
            />
            <NumField
              label="Uglevod"
              unit="g"
              tur="carbs"
              value={natija.uglevod_g}
              onChange={(v) => setNatija({ ...natija, uglevod_g: v })}
            />
            <NumField
              label="Yog'"
              unit="g"
              tur="fat"
              value={natija.yog_g}
              onChange={(v) => setNatija({ ...natija, yog_g: v })}
            />
          </div>

          <button
            className={`fav-toggle ${favSifatidaSaqla ? 'is-on' : ''}`}
            onClick={() => {
              haptic('select')
              setFavSifatidaSaqla((v) => !v)
            }}
          >
            <StarIcon size={17} />
            Sevimlilarga qo'shish
          </button>
        </div>
      )}
    </Sheet>
  )
}
