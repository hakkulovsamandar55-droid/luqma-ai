/** Backend REST API client. Har bir so'rovga Telegram initData biriktiriladi. */

import { getInitData } from './telegram'

const BASE = import.meta.env.VITE_API_BASE || ''

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const kut = (ms) => new Promise((r) => setTimeout(r, ms))

/**
 * Qayta urinish kerakmi.
 *
 * Faqat vaqtinchalik muammolarda urinamiz: internet uzilishi (status 0) va
 * serverning vaqtinchalik xatolari. 4xx larda urinmaymiz — ular qayta
 * yuborganda ham o'zgarmaydi (noto'g'ri ma'lumot, huquq yo'q, chegara tugagan).
 */
function qaytaUrinilsinmi(status, method) {
  // Faqat o'qish so'rovlari xavfsiz takrorlanadi. POST ni takrorlash
  // ikkita bir xil ovqat qo'shib qo'yishi mumkin.
  if (method !== 'GET') return false
  return status === 0 || status === 502 || status === 503 || status === 504
}

async function request(
  path,
  { method = 'GET', body, isForm = false, urinish = 2 } = {}
) {
  const headers = {}
  const initData = getInitData()
  if (initData) headers['Authorization'] = `tma ${initData}`
  if (body && !isForm) headers['Content-Type'] = 'application/json'

  let oxirgiXato = null

  for (let i = 0; i <= urinish; i += 1) {
    let response
    try {
      response = await fetch(`${BASE}${path}`, {
        method,
        headers,
        body: isForm ? body : body ? JSON.stringify(body) : undefined,
      })
    } catch {
      oxirgiXato = new ApiError(
        navigator.onLine === false
          ? "Internet yo'q. Aloqani tekshiring."
          : "Serverga ulanib bo'lmadi. Qayta urinib ko'ring.",
        0
      )
      if (i < urinish && qaytaUrinilsinmi(0, method)) {
        await kut(400 * (i + 1)) // har urinishda biroz ko'proq kutamiz
        continue
      }
      throw oxirgiXato
    }

    if (response.status === 204) return null

    const text = await response.text()
    let data = null
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = null // server HTML xato sahifasi qaytargan bo'lishi mumkin
    }

    if (!response.ok) {
      const detail = data?.detail
      const message =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg).join(', ')
            : `Xatolik (${response.status})`

      oxirgiXato = new ApiError(message, response.status)

      if (i < urinish && qaytaUrinilsinmi(response.status, method)) {
        await kut(400 * (i + 1))
        continue
      }
      throw oxirgiXato
    }

    return data
  }

  throw oxirgiXato
}

/** Sanani API kutadigan YYYY-MM-DD formatiga o'giradi (mahalliy vaqt zonasida). */
export function toApiDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export const api = {
  auth: () => request('/api/auth', { method: 'POST', body: { init_data: getInitData() } }),

  getUser: () => request('/api/user/me'),
  deleteUser: () => request('/api/user/me', { method: 'DELETE' }),
  updateUser: (payload) => request('/api/user/me', { method: 'PUT', body: payload }),
  resetLimits: () => request('/api/user/limits/reset', { method: 'POST' }),

  analyzeImage: (file) => {
    const form = new FormData()
    form.append('rasm', file)
    return request('/api/meals/analyze', { method: 'POST', body: form, isForm: true })
  },
  analyzeText: (matn) =>
    request('/api/meals/analyze-text', { method: 'POST', body: { matn } }),

  createMeal: (payload) => request('/api/meals', { method: 'POST', body: payload }),
  updateMeal: (id, payload) => request(`/api/meals/${id}`, { method: 'PUT', body: payload }),
  deleteMeal: (id) => request(`/api/meals/${id}`, { method: 'DELETE' }),
  getMeals: (date) => request(`/api/meals?date=${date}`),

  getSummary: (date) => request(`/api/stats/summary?date=${date}`),
  getWeekly: (date, kunlar = 7) =>
    request(`/api/stats/weekly?date=${date}&kunlar=${kunlar}`),
  getSuggestion: (date) => request(`/api/stats/suggestion?date=${date}`),

  addWater: (miqdor_ml, sana) =>
    request('/api/water', { method: 'POST', body: { miqdor_ml, sana } }),

  addWeight: (vazn_kg) => request('/api/weight', { method: 'POST', body: { vazn_kg } }),
  getWeights: () => request('/api/weight'),

  // --- Ovqat bazasi ---
  searchFoods: (q) =>
    request(`/api/foods${q ? `?q=${encodeURIComponent(q)}` : ''}`),

  // --- Mashq ---
  getExercises: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v)
    ).toString()
    return request(`/api/exercises${qs ? `?${qs}` : ''}`)
  },
  logExercise: (body) =>
    request('/api/exercise-logs', { method: 'POST', body }),
  getExerciseLogs: (sana) =>
    request(`/api/exercise-logs${sana ? `?sana=${sana}` : ''}`),

  // --- Eslatmalar ---
  getReminders: () => request('/api/reminders'),
  createReminder: (body) => request('/api/reminders', { method: 'POST', body }),
  patchReminder: (id, body) =>
    request(`/api/reminders/${id}`, { method: 'PATCH', body }),
  deleteReminder: (id) => request(`/api/reminders/${id}`, { method: 'DELETE' }),

  // --- Admin: mashq va ovqat ---
  getAdminExercises: () => request('/api/admin/exercises'),
  createExercise: (body) => request('/api/admin/exercises', { method: 'POST', body }),
  patchExercise: (id, body) =>
    request(`/api/admin/exercises/${id}`, { method: 'PATCH', body }),
  deleteExercise: (id) =>
    request(`/api/admin/exercises/${id}`, { method: 'DELETE' }),

  // --- Premium va to'lov ---
  getTariffs: () => request('/api/tariffs'),
  getPaymentInfo: () => request('/api/payment-info'),
  getMyPayments: () => request('/api/payments/me'),
  sendReceipt: (tarifId, file) => {
    const form = new FormData()
    form.append('tarif_id', String(tarifId))
    form.append('chek', file)
    return request('/api/payments', { method: 'POST', body: form, isForm: true })
  },

  // --- Admin: to'lov ---
  getAdminPayments: (holat) =>
    request(`/api/admin/payments${holat ? `?holat=${holat}` : ''}`),
  reviewPayment: (id, tasdiq, izoh) =>
    request(`/api/admin/payments/${id}`, {
      method: 'PATCH',
      body: { tasdiq, izoh },
    }),
  getAdminTariffs: () => request('/api/admin/tariffs'),
  createTarif: (body) => request('/api/admin/tariffs', { method: 'POST', body }),
  patchTarif: (id, body) =>
    request(`/api/admin/tariffs/${id}`, { method: 'PATCH', body }),
  deleteTarif: (id) => request(`/api/admin/tariffs/${id}`, { method: 'DELETE' }),
  getPaymentSettings: () => request('/api/admin/payment-settings'),
  savePaymentSettings: (body) =>
    request('/api/admin/payment-settings', { method: 'PUT', body }),

  // --- Admin ---
  getAdminMe: () => request('/api/admin/me'),
  getAdminStats: () => request('/api/admin/stats'),
  getAdminUsers: (params = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')
    ).toString()
    return request(`/api/admin/users${q ? `?${q}` : ''}`)
  },
  patchAdminUser: (id, body) =>
    request(`/api/admin/users/${id}`, { method: 'PATCH', body }),

  // --- Murabbiy ---
  getChatHistory: (limit = 50) => request(`/api/chat/history?limit=${limit}`),
  sendChat: (matn) => request('/api/chat', { method: 'POST', body: { matn } }),
  clearChat: () => request('/api/chat', { method: 'DELETE' }),
  getCoachTip: () => request('/api/chat/tip'),

  getFavorites: () => request('/api/favorites'),
  addFavorite: (payload) => request('/api/favorites', { method: 'POST', body: payload }),
  deleteFavorite: (id) => request(`/api/favorites/${id}`, { method: 'DELETE' }),
}
