const API_URL = process.env.NEXT_PUBLIC_API_URL ?? ''

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : ''
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  dashboard: () => apiFetch('/admin/dashboard'),
  groups: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiFetch(`/admin/groups${q}`)
  },
  group: (id: number) => apiFetch(`/admin/groups/${id}`),
  addNote: (id: number, text: string) =>
    apiFetch(`/admin/groups/${id}/notes`, { method: 'POST', body: JSON.stringify({ text }) }),
  updateTariff: (id: number, plan: string, duration_days?: number) =>
    apiFetch(`/admin/groups/${id}/tariff`, {
      method: 'PATCH',
      body: JSON.stringify({ plan, duration_days }),
    }),
  blockGroup: (id: number) => apiFetch(`/admin/groups/${id}/block`, { method: 'PATCH' }),
  unblockGroup: (id: number) => apiFetch(`/admin/groups/${id}/unblock`, { method: 'PATCH' }),
  usageAnalytics: () => apiFetch('/admin/analytics/usage'),
  funnel: () => apiFetch('/admin/analytics/funnel'),
  systemLogs: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiFetch(`/logs/system${q}`)
  },
}
