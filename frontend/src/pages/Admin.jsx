import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'
import { raqam } from '../lib/format'
import { haptic, showAlert, showConfirm } from '../lib/telegram'
import './Admin.css'

const FILTRLAR = [
  { key: '', label: 'Hammasi' },
  { key: 'premium', label: 'Premium' },
  { key: 'admin', label: 'Admin' },
  { key: 'bloklangan', label: 'Bloklangan' },
]

const PREMIUM_MUDDATLAR = [
  { kun: 30, label: '30 kun' },
  { kun: 90, label: '90 kun' },
  { kun: 365, label: '1 yil' },
  { kun: 0, label: 'Muddatsiz' },
]

function sana(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`
}

/** Statistika kartochkasi. */
function Stat({ label, value, izoh }) {
  return (
    <div className="astat">
      <div className="astat-value num">{raqam(value)}</div>
      <div className="astat-label">{label}</div>
      {izoh && <div className="astat-note">{izoh}</div>}
    </div>
  )
}

/** Bitta foydalanuvchi ustida amallar — pastdan chiqadigan oyna. */
function UserSheet({ user, onClose, onChange }) {
  const [ish, setIsh] = useState(false)

  async function ozgartir(body, tasdiq) {
    if (tasdiq && !(await showConfirm(tasdiq))) return

    setIsh(true)
    haptic('light')
    try {
      const yangi = await api.patchAdminUser(user.id, body)
      onChange(yangi)
    } catch (e) {
      showAlert(e.message)
    } finally {
      setIsh(false)
    }
  }

  const himoyalangan = user.asosiy_admin

  return (
    <>
      <div className="asheet-veil" onClick={onClose} />
      <div className="asheet">
        <div className="asheet-grip" />

        <div className="asheet-head">
          <div>
            <b>{user.ism || 'Ismsiz'}</b>
            <span>
              {user.username ? `@${user.username} · ` : ''}ID {user.telegram_id}
            </span>
          </div>
        </div>

        <div className="asheet-facts">
          <div>
            <span>Qo'shilgan</span>
            <b className="num">{sana(user.created_at)}</b>
          </div>
          <div>
            <span>Oxirgi faollik</span>
            <b className="num">{sana(user.oxirgi_faollik)}</b>
          </div>
          <div>
            <span>Ovqatlar</span>
            <b className="num">{raqam(user.ovqatlar_soni)}</b>
          </div>
        </div>

        {himoyalangan && (
          <p className="asheet-warn">
            Bu asosiy admin (.env dagi ADMIN_IDS). Uni bu yerdan
            o'zgartirib bo'lmaydi.
          </p>
        )}

        {/* --- Premium --- */}
        <div className="asheet-block">
          <div className="asheet-title">
            Premium
            {user.premium_faolmi && (
              <span className="badge">
                {user.premium_tugash
                  ? `${sana(user.premium_tugash)} gacha`
                  : 'muddatsiz'}
              </span>
            )}
          </div>

          {user.is_premium ? (
            <button
              className="abtn abtn-soft"
              disabled={ish}
              onClick={() => ozgartir({ is_premium: false }, 'Premium olib tashlansinmi?')}
            >
              Premiumni olib tashlash
            </button>
          ) : (
            <div className="achips">
              {PREMIUM_MUDDATLAR.map((m) => (
                <button
                  key={m.kun}
                  className="achip"
                  disabled={ish}
                  onClick={() => ozgartir({ is_premium: true, premium_kun: m.kun })}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* --- Admin --- */}
        <div className="asheet-block">
          <div className="asheet-title">Adminlik</div>
          <button
            className="abtn abtn-soft"
            disabled={ish || himoyalangan}
            onClick={() =>
              ozgartir(
                { is_admin: !user.is_admin },
                user.is_admin
                  ? 'Adminlik olib tashlansinmi?'
                  : 'Bu odam admin qilinsinmi? U hamma foydalanuvchini boshqara oladi.'
              )
            }
          >
            {user.is_admin ? 'Adminlikdan chiqarish' : 'Admin qilish'}
          </button>
        </div>

        {/* --- Blok --- */}
        <div className="asheet-block">
          <div className="asheet-title">Bloklash</div>
          {user.is_blocked && user.block_sabab && (
            <p className="asheet-reason">Sabab: {user.block_sabab}</p>
          )}
          <button
            className={`abtn ${user.is_blocked ? 'abtn-soft' : 'abtn-danger'}`}
            disabled={ish || himoyalangan}
            onClick={() => {
              if (user.is_blocked) {
                ozgartir({ is_blocked: false }, 'Blok olib tashlansinmi?')
              } else {
                ozgartir(
                  {
                    is_blocked: true,
                    block_sabab: 'Qoidalar buzilgani uchun bloklandi',
                  },
                  'Bloklansinmi? U ilovadan umuman foydalana olmaydi.'
                )
              }
            }}
          >
            {user.is_blocked ? 'Blokdan chiqarish' : 'Bloklash'}
          </button>
        </div>

        <button className="abtn abtn-ghost" onClick={onClose}>
          Yopish
        </button>
      </div>
    </>
  )
}

/** Kutayotgan to'lov arizalari. */
function Payments() {
  const [royxat, setRoyxat] = useState([])
  const [holat, setHolat] = useState('kutilmoqda')
  const [ochiq, setOchiq] = useState(null)
  const [ish, setIsh] = useState(false)

  const yukla = useCallback(() => {
    api
      .getAdminPayments(holat)
      .then((r) => setRoyxat(Array.isArray(r) ? r : []))
      .catch(() => setRoyxat([]))
  }, [holat])

  useEffect(yukla, [yukla])

  async function qaror(p, tasdiq) {
    const savol = tasdiq
      ? `Tasdiqlansinmi? ${p.tarif_nom} (${raqam(p.tarif_kun)} kun) beriladi.`
      : 'Rad etilsinmi? Avtomatik berilgan premium olib qo\u2019yiladi.'
    if (!(await showConfirm(savol))) return

    setIsh(true)
    haptic('light')
    try {
      await api.reviewPayment(p.id, tasdiq, null)
      setOchiq(null)
      yukla()
    } catch (e) {
      showAlert(e.message)
    } finally {
      setIsh(false)
    }
  }

  return (
    <>
      <div className="afiltrs">
        {['kutilmoqda', 'tasdiqlangan', 'rad_etilgan'].map((h) => (
          <button
            key={h}
            className={`afiltr ${holat === h ? 'is-on' : ''}`}
            onClick={() => setHolat(h)}
          >
            {h === 'kutilmoqda'
              ? 'Kutilmoqda'
              : h === 'tasdiqlangan'
                ? 'Tasdiqlangan'
                : 'Rad etilgan'}
          </button>
        ))}
      </div>

      {royxat.length === 0 ? (
        <p className="abosh">Ariza yo'q</p>
      ) : (
        <div className="alist" style={{ marginTop: 14 }}>
          {royxat.map((p) => (
            <button key={p.id} className="arow" onClick={() => setOchiq(p)}>
              <div className="arow-main">
                <span className="arow-name">
                  {p.user_ism || 'Ismsiz'}
                  {p.avto_otdi ? (
                    <i className="tag">avto</i>
                  ) : (
                    <i className="tag tag-block">qo'lda</i>
                  )}
                </span>
                <span className="arow-sub num">
                  {p.tarif_nom} · {raqam(p.kutilgan_summa)} so'm
                </span>
              </div>
              <span className="arow-chev">›</span>
            </button>
          ))}
        </div>
      )}

      {ochiq && (
        <>
          <div className="asheet-veil" onClick={() => setOchiq(null)} />
          <div className="asheet">
            <div className="asheet-grip" />
            <div className="asheet-head">
              <div>
                <b>{ochiq.user_ism || 'Ismsiz'}</b>
                <span>ID {ochiq.user_telegram_id}</span>
              </div>
            </div>

            <div className="asheet-facts">
              <div>
                <span>Tarif</span>
                <b>{ochiq.tarif_nom}</b>
              </div>
              <div>
                <span>Kutilgan</span>
                <b className="num">{raqam(ochiq.kutilgan_summa)}</b>
              </div>
              <div>
                <span>Topilgan</span>
                <b className="num">
                  {ochiq.aniqlangan_summa ? raqam(ochiq.aniqlangan_summa) : '—'}
                </b>
              </div>
            </div>

            <p className="asheet-warn">
              Avtomatik tekshiruv: {ochiq.tekshiruv_izoh || '—'}
            </p>

            {ochiq.chek_yoli && (
              <div className="asheet-block">
                <div className="asheet-title">Chek</div>
                <img className="acheck" src={ochiq.chek_yoli} alt="Chek" />
              </div>
            )}

            {ochiq.ai_matn && (
              <div className="asheet-block">
                <div className="asheet-title">Rasmdan o'qilgan matn</div>
                <pre className="araw">{ochiq.ai_matn}</pre>
              </div>
            )}

            {ochiq.holat === 'kutilmoqda' && (
              <div className="asheet-block">
                <button
                  className="abtn abtn-soft"
                  disabled={ish}
                  onClick={() => qaror(ochiq, true)}
                >
                  Tasdiqlash
                </button>
                <button
                  className="abtn abtn-danger"
                  style={{ marginTop: 8 }}
                  disabled={ish}
                  onClick={() => qaror(ochiq, false)}
                >
                  Rad etish
                </button>
              </div>
            )}

            <button className="abtn abtn-ghost" onClick={() => setOchiq(null)}>
              Yopish
            </button>
          </div>
        </>
      )}
    </>
  )
}

/** Tariflar va to'lov rekvizitlari — admin paneldan boshqariladi. */
function Tariffs() {
  const [royxat, setRoyxat] = useState([])
  const [sozlama, setSozlama] = useState(null)
  const [tahrir, setTahrir] = useState(null) // tarif obyekti yoki 'yangi'
  const [ish, setIsh] = useState(false)

  const yukla = useCallback(() => {
    api
      .getAdminTariffs()
      .then((r) => setRoyxat(Array.isArray(r) ? r : []))
      .catch(() => setRoyxat([]))
    api.getPaymentSettings().then(setSozlama).catch(() => {})
  }, [])

  useEffect(yukla, [yukla])

  async function saqla(t) {
    setIsh(true)
    try {
      if (t.id) await api.patchTarif(t.id, t)
      else await api.createTarif(t)
      setTahrir(null)
      yukla()
    } catch (e) {
      showAlert(e.message)
    } finally {
      setIsh(false)
    }
  }

  async function ochir(t) {
    if (!(await showConfirm(`"${t.nom}" tarifi o'chirilsinmi?`))) return
    try {
      await api.deleteTarif(t.id)
      setTahrir(null)
      yukla()
    } catch (e) {
      showAlert(e.message)
    }
  }

  async function sozlamaSaqla(e) {
    e.preventDefault()
    const f = new FormData(e.target)
    setIsh(true)
    try {
      const r = await api.savePaymentSettings({
        karta_raqam: f.get('karta_raqam'),
        karta_egasi: f.get('karta_egasi'),
        chek_amal_kuni: Number(f.get('chek_amal_kuni')) || 3,
        yordam_username: f.get('yordam_username'),
        izoh: f.get('izoh') || null,
        premium_sarlavha: f.get('premium_sarlavha'),
        premium_afzalliklar: f.get('premium_afzalliklar'),
      })
      setSozlama(r)
      showAlert('Saqlandi')
    } catch (err) {
      showAlert(err.message)
    } finally {
      setIsh(false)
    }
  }

  return (
    <>
      <div className="alist-head">
        <h2 className="section-title">Tariflar</h2>
        <button className="aadd" onClick={() => setTahrir({})}>
          + Qo'shish
        </button>
      </div>

      {royxat.length === 0 ? (
        <p className="abosh">Tarif yo'q. "+ Qo'shish" bilan yarating.</p>
      ) : (
        <div className="alist">
          {royxat.map((t) => (
            <button key={t.id} className="arow" onClick={() => setTahrir(t)}>
              <div className="arow-main">
                <span className="arow-name">
                  {t.nom}
                  {!t.faol && <i className="tag tag-block">o'chiq</i>}
                </span>
                <span className="arow-sub num">
                  {raqam(t.kun)} kun · {raqam(t.narx)} so'm
                </span>
              </div>
              <span className="arow-chev">›</span>
            </button>
          ))}
        </div>
      )}

      <h2 className="section-title alist-head">To'lov rekvizitlari</h2>
      {sozlama && (
        <form className="aform" onSubmit={sozlamaSaqla}>
          <label>
            <span>Karta raqami</span>
            <input name="karta_raqam" defaultValue={sozlama.karta_raqam} />
          </label>
          <label>
            <span>Karta egasi</span>
            <input name="karta_egasi" defaultValue={sozlama.karta_egasi} />
          </label>
          <label>
            <span>Chek amal muddati (kun)</span>
            <input
              name="chek_amal_kuni"
              type="number"
              min="1"
              max="90"
              defaultValue={sozlama.chek_amal_kuni}
            />
          </label>
          <label>
            <span>Yordam uchun Telegram username</span>
            <input
              name="yordam_username"
              placeholder="luqma_admin"
              defaultValue={sozlama.yordam_username}
            />
          </label>
          <label>
            <span>Izoh (ixtiyoriy)</span>
            <input name="izoh" defaultValue={sozlama.izoh || ''} />
          </label>

          <label>
            <span>Premium oynasi sarlavhasi</span>
            <input
              name="premium_sarlavha"
              defaultValue={sozlama.premium_sarlavha || ''}
              placeholder="Premium bilan ko'proq imkoniyat"
            />
          </label>
          <label>
            <span>Afzalliklar (har qator — bitta band)</span>
            <textarea
              name="premium_afzalliklar"
              rows={5}
              defaultValue={sozlama.premium_afzalliklar || ''}
              placeholder={'Cheksiz kaloriya tahlili\nAI murabbiy\nKengaytirilgan chegaralar'}
            />
          </label>

          <button className="abtn abtn-primary" disabled={ish}>
            Saqlash
          </button>
        </form>
      )}

      {tahrir && (
        <>
          <div className="asheet-veil" onClick={() => setTahrir(null)} />
          <div className="asheet">
            <div className="asheet-grip" />
            <div className="asheet-head">
              <div>
                <b>{tahrir.id ? 'Tarifni tahrirlash' : 'Yangi tarif'}</b>
              </div>
            </div>

            <form
              className="aform"
              onSubmit={(e) => {
                e.preventDefault()
                const f = new FormData(e.target)
                saqla({
                  id: tahrir.id,
                  nom: f.get('nom'),
                  kun: Number(f.get('kun')),
                  narx: Number(f.get('narx')),
                  tavsif: f.get('tavsif') || null,
                  faol: f.get('faol') === 'on',
                  tartib: Number(f.get('tartib')) || 0,
                })
              }}
            >
              <label>
                <span>Nom</span>
                <input name="nom" defaultValue={tahrir.nom || ''} placeholder="Pro" required />
              </label>
              <label>
                <span>Necha kun</span>
                <input name="kun" type="number" min="1" defaultValue={tahrir.kun || 30} required />
              </label>
              <label>
                <span>Narx (so'm)</span>
                <input name="narx" type="number" min="0" defaultValue={tahrir.narx || 0} required />
              </label>
              <label>
                <span>Tavsif (ixtiyoriy)</span>
                <input name="tavsif" defaultValue={tahrir.tavsif || ''} placeholder="Eng ommabop" />
              </label>
              <label>
                <span>Tartib</span>
                <input name="tartib" type="number" defaultValue={tahrir.tartib || 0} />
              </label>
              <label className="acheck">
                <input
                  name="faol"
                  type="checkbox"
                  defaultChecked={tahrir.id ? tahrir.faol : true}
                />
                <span>Faol (foydalanuvchilarga ko'rinsin)</span>
              </label>

              <button className="abtn abtn-primary" disabled={ish}>
                Saqlash
              </button>
            </form>

            {tahrir.id && (
              <button className="abtn abtn-danger" onClick={() => ochir(tahrir)}>
                O'chirish
              </button>
            )}
            <button className="abtn abtn-ghost" onClick={() => setTahrir(null)}>
              Yopish
            </button>
          </div>
        </>
      )}
    </>
  )
}

export default function Admin({ onBack }) {
  const [bolim, setBolim] = useState('umumiy')
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [jami, setJami] = useState(0)
  const [q, setQ] = useState('')
  const [filtr, setFiltr] = useState('')
  const [tanlangan, setTanlangan] = useState(null)
  const [yuklanmoqda, setYuklanmoqda] = useState(true)
  const [xato, setXato] = useState(null)

  useEffect(() => {
    api.getAdminStats().then(setStats).catch((e) => setXato(e.message))
  }, [])

  const yukla = useCallback(async () => {
    setYuklanmoqda(true)
    try {
      const r = await api.getAdminUsers({ q, filtr, limit: 50 })
      setUsers(Array.isArray(r?.foydalanuvchilar) ? r.foydalanuvchilar : [])
      setJami(r?.jami || 0)
    } catch (e) {
      setXato(e.message)
    } finally {
      setYuklanmoqda(false)
    }
  }, [q, filtr])

  // Qidiruvda har harfda so'rov yubormaymiz.
  useEffect(() => {
    const t = setTimeout(yukla, q ? 350 : 0)
    return () => clearTimeout(t)
  }, [yukla, q])

  function yangilandi(yangi) {
    setUsers((old) => old.map((u) => (u.id === yangi.id ? yangi : u)))
    setTanlangan(yangi)
    api.getAdminStats().then(setStats).catch(() => {})
  }

  return (
    <div className="admin">
      <header className="admin-head">
        <button className="admin-back" onClick={onBack} aria-label="Orqaga">
          <svg viewBox="0 0 24 24" width="21" height="21">
            <path d="M15 18l-6-6 6-6" fill="none" stroke="currentColor"
                  strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <h1>Admin panel</h1>
      </header>

      <div className="admin-body">
        <div className="atabs">
          {[
            ['umumiy', 'Umumiy'],
            ['tolov', "To'lovlar"],
            ['tarif', 'Tariflar'],
          ].map(([k, nom]) => (
            <button
              key={k}
              className={`atab ${bolim === k ? 'is-on' : ''}`}
              onClick={() => {
                haptic('light')
                setBolim(k)
              }}
            >
              {nom}
            </button>
          ))}
        </div>

        {bolim === 'tolov' && <Payments />}

        {bolim === 'tarif' && <Tariffs />}

        {bolim === 'umumiy' && xato && <p className="admin-error">{xato}</p>}

        {bolim === 'umumiy' && stats && (
          <>
            <div className="astats">
              <Stat label="Jami foydalanuvchi" value={stats.jami_foydalanuvchi} />
              <Stat
                label="Bugun faol"
                value={stats.faol_bugun}
                izoh={`Haftada ${raqam(stats.faol_hafta)}`}
              />
              <Stat
                label="Yangi bugun"
                value={stats.yangi_bugun}
                izoh={`Haftada ${raqam(stats.yangi_hafta)}`}
              />
              <Stat label="Bugungi ovqatlar" value={stats.bugun_ovqat} />
              <Stat label="Premium" value={stats.premium_soni} />
              <Stat label="Bloklangan" value={stats.bloklangan_soni} />
            </div>

            <div className="abudget">
              <div className="abudget-top">
                <span>Bugungi AI chaqiruvlari</span>
                <b className="num">
                  {raqam(stats.bugun_ai_chaqiruv)}
                  {stats.umumiy_kunlik_limit > 0 && (
                    <i> / {raqam(stats.umumiy_kunlik_limit)}</i>
                  )}
                </b>
              </div>
              {stats.umumiy_kunlik_limit > 0 && (
                <div className="abudget-bar">
                  <span
                    style={{
                      width: `${Math.min(100, (stats.bugun_ai_chaqiruv / stats.umumiy_kunlik_limit) * 100)}%`,
                    }}
                  />
                </div>
              )}
            </div>
          </>
        )}

        {bolim === 'umumiy' && (
        <>
        <input
          className="asearch"
          type="search"
          placeholder="Ism, username yoki ID bo'yicha qidirish"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />

        <div className="afiltrs">
          {FILTRLAR.map((f) => (
            <button
              key={f.key}
              className={`afiltr ${filtr === f.key ? 'is-on' : ''}`}
              onClick={() => {
                haptic('light')
                setFiltr(f.key)
              }}
            >
              {f.label}
            </button>
          ))}
        </div>

        <div className="alist-head">
          <h2 className="section-title">Foydalanuvchilar</h2>
          <span className="num">{raqam(jami)}</span>
        </div>

        {yuklanmoqda && users.length === 0 ? (
          <p className="abosh">Yuklanmoqda…</p>
        ) : users.length === 0 ? (
          <p className="abosh">Hech kim topilmadi</p>
        ) : (
          <div className="alist">
            {users.map((u) => (
              <button
                key={u.id}
                className="arow"
                onClick={() => {
                  haptic('light')
                  setTanlangan(u)
                }}
              >
                <div className="arow-main">
                  <span className="arow-name">
                    {u.ism || 'Ismsiz'}
                    {u.is_blocked && <i className="tag tag-block">blok</i>}
                    {u.premium_faolmi && <i className="tag">premium</i>}
                    {(u.is_admin || u.asosiy_admin) && <i className="tag">admin</i>}
                  </span>
                  <span className="arow-sub num">
                    {u.username ? `@${u.username}` : u.telegram_id}
                  </span>
                </div>
                <span className="arow-meals num">{raqam(u.ovqatlar_soni)}</span>
                <span className="arow-chev">›</span>
              </button>
            ))}
          </div>
        )}
        </>
        )}
      </div>

      {tanlangan && (
        <UserSheet
          user={tanlangan}
          onClose={() => setTanlangan(null)}
          onChange={yangilandi}
        />
      )}
    </div>
  )
}
