'use client'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { miniApi } from '@/lib/api'
import ChatNav from '@/components/ChatNav'

export default function ModerationPage() {
  const params = useParams()
  const chatId = Number(params.id)
  const router = useRouter()
  const [settings, setSettings] = useState<any>(null)
  const [punishments, setPunishments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([miniApi.settings(chatId), miniApi.punishments(chatId)])
      .then(([s, p]) => { setSettings(s); setPunishments(Array.isArray(p) ? p.slice(0, 10) : []) })
      .catch(console.error).finally(() => setLoading(false))
  }, [chatId])

  async function save(patch: Record<string, unknown>) {
    setSaving(true)
    const updated = await miniApi.updateSettings(chatId, patch)
    setSettings(updated)
    setSaving(false)
  }

  if (loading) return <div className="page"><div className="spinner" /></div>

  const TYPE_BADGE: Record<string, string> = { ban: 'badge-red', mute: 'badge-yellow', kick: 'badge-grey' }
  const STATUS_BADGE: Record<string, string> = { active: 'badge-red', expired: 'badge-grey', revoked: 'badge-grey' }

  return (
    <div className="page">
      <div className="topbar">
        <button className="topbar-back" onClick={() => router.push(`/chat/${chatId}`)}>←</button>
        <div>
          <div className="topbar-title">Модерация</div>
          <div className="topbar-subtitle">{saving ? 'Сохранение...' : 'Настройки'}</div>
        </div>
      </div>

      <div className="page-content fade-in">
        {/* Warn limits */}
        <div className="section">
          <div className="section-label">Предупреждения</div>
          <div className="glass">
            <div className="setting-row">
              <div className="setting-info">
                <div className="setting-title">Лимит варнов</div>
                <div className="setting-desc">При достижении — автоматическое наказание</div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {[1,2,3,5].map(n => (
                  <button key={n} onClick={() => save({ default_warn_limit: n })}
                    style={{
                      width: 36, height: 36, borderRadius: 8, border: 'none', cursor: 'pointer',
                      background: settings?.default_warn_limit === n ? 'var(--accent)' : 'var(--glass-bg-light)',
                      color: settings?.default_warn_limit === n ? '#fff' : 'var(--text-2)',
                      fontWeight: 600, fontSize: 14,
                    }}>
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <div className="setting-row">
              <div className="setting-info">
                <div className="setting-title">Действие при лимите</div>
                <div className="setting-desc">Что происходит когда варны заканчиваются</div>
              </div>
              <select
                value={settings?.warn_limit_action || 'mute'}
                onChange={e => save({ warn_limit_action: e.target.value })}
                className="field" style={{ width: 'auto', padding: '6px 10px' }}
              >
                <option value="mute">Мут</option>
                <option value="ban">Бан</option>
              </select>
            </div>
            <div className="setting-row">
              <div className="setting-info">
                <div className="setting-title">Длительность мута</div>
                <div className="setting-desc">По умолчанию при выдаче /mute</div>
              </div>
              <select
                value={String(settings?.default_mute_duration || 3600)}
                onChange={e => save({ default_mute_duration: Number(e.target.value) })}
                className="field" style={{ width: 'auto', padding: '6px 10px' }}
              >
                <option value="600">10 мин</option>
                <option value="1800">30 мин</option>
                <option value="3600">1 час</option>
                <option value="21600">6 часов</option>
                <option value="86400">1 день</option>
                <option value="604800">7 дней</option>
              </select>
            </div>
          </div>
        </div>

        {/* Recent punishments */}
        <div className="section">
          <div className="section-label">Последние наказания</div>
          {punishments.length === 0 ? (
            <div className="empty"><div className="empty-icon">🛡️</div>Нарушений нет</div>
          ) : (
            <div className="glass">
              {punishments.map((p: any) => (
                <div key={p.id} className="list-item">
                  <div className="list-icon" style={{ fontSize: 18 }}>
                    {p.type === 'ban' ? '🔨' : p.type === 'mute' ? '🔇' : '👢'}
                  </div>
                  <div className="list-body">
                    <div className="list-title">User #{p.user_id}</div>
                    <div className="list-sub">{p.reason || 'Без причины'}</div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
                    <span className={`badge ${TYPE_BADGE[p.type] || 'badge-grey'}`}>{p.type}</span>
                    <span className={`badge ${STATUS_BADGE[p.status] || 'badge-grey'}`} style={{ fontSize: 10 }}>{p.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      <ChatNav chatId={chatId} />
    </div>
  )
}


