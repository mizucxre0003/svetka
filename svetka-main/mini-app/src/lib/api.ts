const API_URL = process.env.NEXT_PUBLIC_MINI_APP_API_URL ?? ''

async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })
  if (!res.ok) throw new Error(`API ${res.status}`)
  return res.json()
}

// Получить telegram user id из Telegram WebApp
export function getTelegramUserId(): number | null {
  if (typeof window === 'undefined') return null
  const tg = (window as any).Telegram?.WebApp
  return tg?.initDataUnsafe?.user?.id ?? null
}

export const miniApi = {
  chats: (telegramUserId: number) =>
    apiFetch(`/chats/?telegram_user_id=${telegramUserId}`),
  chat: (id: number) => apiFetch(`/chats/${id}`),
  settings: (chatId: number) => apiFetch(`/settings/${chatId}`),
  updateSettings: (chatId: number, data: Record<string, unknown>) =>
    apiFetch(`/settings/${chatId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  triggers: (chatId: number) => apiFetch(`/triggers/${chatId}`),
  createTrigger: (chatId: number, data: Record<string, unknown>) =>
    apiFetch(`/triggers/${chatId}`, { method: 'POST', body: JSON.stringify(data) }),
  updateTrigger: (triggerId: number, data: Record<string, unknown>) =>
    apiFetch(`/triggers/${triggerId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTrigger: (triggerId: number) =>
    apiFetch(`/triggers/${triggerId}`, { method: 'DELETE' }),
  analytics: (chatId: number, days = 7) =>
    apiFetch(`/analytics/${chatId}/summary?days=${days}`),
  logs: (chatId: number, actionType?: string) => {
    const q = actionType ? `?action_type=${actionType}` : ''
    return apiFetch(`/logs/chat/${chatId}${q}`)
  },
  punishments: (chatId: number) =>
    apiFetch(`/moderation/punishments/${chatId}?active_only=false`),
  warns: (chatId: number, userId: number) =>
    apiFetch(`/moderation/warns/${chatId}/${userId}`),
}
