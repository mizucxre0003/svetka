'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { miniApi, getTelegramUserId } from '@/lib/api'

export default function ChatsPage() {
  const [chats, setChats] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const tg = (window as any).Telegram?.WebApp
    tg?.ready?.()
    const uid = getTelegramUserId() ?? 0
    if (!uid) { setLoading(false); return }
    miniApi.chats(uid).then(data => setChats(Array.isArray(data) ? data : [])).catch(console.error).finally(() => setLoading(false))
  }, [])

  const STATUS: Record<string,string> = { active: 'badge-green', inactive: 'badge-yellow', blocked: 'badge-red' }
  const PLAN: Record<string,string> = { free: 'badge-grey', trial: 'badge-yellow', pro: 'badge-accent' }

  return (
    <div className="page">
      {/* Header */}
      <div className="topbar">
        <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg,#6c72ff,#a78bfa)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>✦</div>
        <div>
          <div className="topbar-title" style={{ fontSize: 17 }}>Svetka</div>
          <div className="topbar-subtitle">Мои группы</div>
        </div>
      </div>

      <div className="page-content fade-in">
        {loading ? (
          <div className="spinner" />
        ) : chats.length === 0 ? (
          <div style={{ marginTop: 60 }}>
            <div className="empty">
              <div className="empty-icon">◎</div>
              <div style={{ fontWeight: 600, marginBottom: 6, color: 'var(--text-2)' }}>Групп нет</div>
              <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Добавьте Svetka в Telegram-группу и выдайте права администратора</div>
            </div>
          </div>
        ) : (
          <div className="section">
            <div className="section-label">Подключённые группы · {chats.length}</div>
            <div className="glass">
              {chats.map((chat, i) => (
                <Link key={chat.id} href={`/chat/${chat.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="list-item">
                    <div className="list-icon" style={{ fontSize: 22 }}>
                      {chat.title?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div className="list-body">
                      <div className="list-title">{chat.title}</div>
                      <div className="list-sub">
                        {chat.username ? `@${chat.username} · ` : ''}{chat.member_count?.toLocaleString() ?? 0} участников
                      </div>
                    </div>
                    <div className="list-right" style={{ flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                      <span className={`badge ${PLAN[chat.tariff] || 'badge-grey'}`}>{chat.tariff}</span>
                      <span className={`badge ${STATUS[chat.status] || 'badge-grey'}`} style={{ fontSize: 10 }}>{chat.status}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Info box */}
        <div className="glass-sm" style={{ padding: '14px 16px', marginTop: 12, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <span style={{ fontSize: 20 }}>💡</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 3 }}>Как добавить группу?</div>
            <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>
              Найдите @SvetkaBot в Telegram, добавьте его в группу как администратора с полными правами.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
