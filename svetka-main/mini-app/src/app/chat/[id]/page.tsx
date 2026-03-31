'use client'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import { miniApi } from '@/lib/api'
import ChatNav from '@/components/ChatNav'

export default function ChatDashboard() {
  const params = useParams()
  const chatId = Number(params.id)
  const router = useRouter()
  const [chat, setChat] = useState<any>(null)
  const [settings, setSettings] = useState<any>(null)
  const [analytics, setAnalytics] = useState<any>(null)
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      miniApi.chat(chatId),
      miniApi.settings(chatId),
      miniApi.analytics(chatId, 7),
      miniApi.logs(chatId),
    ]).then(([c, s, a, l]) => {
      setChat(c); setSettings(s); setAnalytics(a)
      setLogs(Array.isArray(l) ? l.slice(0, 5) : [])
    }).catch(console.error).finally(() => setLoading(false))
  }, [chatId])

  if (loading) return <div className="page"><div className="spinner" /></div>

  const modules = [
    { key: 'welcome_enabled', label: 'Приветствие', icon: '👋', href: `/chat/${chatId}/messages` },
    { key: 'anti_flood_enabled', label: 'Антифлуд', icon: '🌊', href: `/chat/${chatId}/protection` },
    { key: 'anti_links_enabled', label: 'Антиссылки', icon: '🔗', href: `/chat/${chatId}/protection` },
    { key: 'stop_words_enabled', label: 'Стоп-слова', icon: '🚫', href: `/chat/${chatId}/protection` },
    { key: 'caps_filter_enabled', label: 'Капс-фильтр', icon: '🔠', href: `/chat/${chatId}/protection` },
    { key: 'triggers_enabled', label: 'Триггеры', icon: '⚡', href: `/chat/${chatId}/messages` },
  ]

  return (
    <div className="page">
      <div className="topbar">
        <button className="topbar-back" onClick={() => router.push('/')}>←</button>
        <div>
          <div className="topbar-title">{chat?.title || 'Группа'}</div>
          <div className="topbar-subtitle">Дашборд</div>
        </div>
      </div>

      <div className="page-content fade-in">
        {/* Stats */}
        {analytics && (
          <div className="section">
            <div className="section-label">За 7 дней</div>
            <div className="glass">
              <div className="stat-grid">
                {[
                  ['💬', analytics.messages ?? 0, 'Сообщений'],
                  ['⚠️', analytics.warnings ?? 0, 'Предупреждений'],
                  ['🔇', analytics.mutes ?? 0, 'Мутов'],
                  ['🔨', analytics.bans ?? 0, 'Банов'],
                ].map(([icon, val, lbl]) => (
                  <div key={String(lbl)} className="stat-cell glass-sm" style={{ margin: 8, borderRadius: 12 }}>
                    <div style={{ fontSize: 22 }}>{icon}</div>
                    <div className="stat-num">{String(val)}</div>
                    <div className="stat-lbl">{String(lbl)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Modules */}
        <div className="section">
          <div className="section-label">Модули</div>
          <div className="glass">
            {modules.map(m => (
              <Link key={m.key} href={m.href} style={{ textDecoration: 'none', color: 'inherit' }}>
                <div className="list-item">
                  <div className="list-icon" style={{ fontSize: 20 }}>{m.icon}</div>
                  <div className="list-body">
                    <div className="list-title">{m.label}</div>
                  </div>
                  <div className="list-right">
                    <span className={`status-dot ${settings?.[m.key] ? 'status-on' : 'status-off'}`} />
                    <span style={{ fontSize: 12, color: settings?.[m.key] ? 'var(--green)' : 'var(--text-3)' }}>
                      {settings?.[m.key] ? 'Вкл' : 'Выкл'}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent logs */}
        {logs.length > 0 && (
          <div className="section">
            <div className="section-label">Последние события</div>
            <div className="glass">
              {logs.map((l, i) => (
                <div key={i} className="log-item">
                  <div className={`log-dot ${l.action_type.includes('ban') || l.action_type.includes('mute') ? 'log-dot-mod' : l.action_type.includes('protect') ? 'log-dot-protect' : 'log-dot-sys'}`} />
                  <div className="log-body">
                    <div className="log-action">{l.action_type.replace(/_/g, ' ')}</div>
                    <div className="log-time">{new Date(l.created_at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</div>
                  </div>
                </div>
              ))}
              <Link href={`/chat/${chatId}/logs`} style={{ textDecoration: 'none' }}>
                <div style={{ padding: '12px 16px', textAlign: 'center', fontSize: 13, color: 'var(--accent)', borderTop: '1px solid var(--glass-border)' }}>
                  Все логи →
                </div>
              </Link>
            </div>
          </div>
        )}
      </div>
      <ChatNav chatId={chatId} />
    </div>
  )
}


