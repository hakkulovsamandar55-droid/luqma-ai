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

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const headers = {}
  const initData = getInitData()
  if (initData) headers['Authorization'] = `tma ${initData}`
  if (body && !isForm) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: isForm ? body : body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError("Internet aloqasi yo'q", 0)
  }

  if (response.status === 204) return null

  const text = await response.text()
  const data = text ? JSON.parse(text) : null

  if (!response.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg).join(', ')
          : `Xatolik (${response.status})`
    throw new ApiError(message, response.status)
  }
  return data
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

  getFavorites: () => request('/api/favorites'),
  addFavorite: (payload) => request('/api/favorites', { method: 'POST', body: payload }),
  deleteFavorite: (id) => request(`/api/favorites/${id}`, { method: 'DELETE' }),
}
