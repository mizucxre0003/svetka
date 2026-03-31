'use client'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import ChatNav from '@/components/ChatNav'

const ROLE_ICONS: Record<string, string> = { owner: '👑', admin: '⚙️', moderator: '🛡️', member: '👤' }
const ROLE_COLORS: Record<string, string> = { owner: 'var(--yellow)', admin: 'var(--accent)', moderator: 'var(--green)', member: 'var(--text-3)' }

const RIGHTS = [
  { key: 'can_ban', label: 'Банить пользователей' },
  { key: 'can_mute', label: 'Выдавать мут' },
  { key: 'can_warn', label: 'Выдавать предупреждения' },
  { key: 'can_edit_welcome', label: 'Редактировать приветствие' },
  { key: 'can_edit_rules', label: 'Редактировать правила' },
  { key: 'can_manage_protection', label: 'Управлять защитой' },
  { key: 'can_manage_triggers', label: 'Управлять триггерами' },
  { key: 'can_view_logs', label: 'Просматривать логи' },
  { key: 'can_view_stats', label: 'Просматривать статистику' },
]

const PRESET_RIGHTS: Record<string, string[]> = {
  owner: RIGHTS.map(r => r.key),
  admin: RIGHTS.map(r => r.key),
  moderator: ['can_mute', 'can_warn', 'can_view_logs'],
  member: [],
}

export default function RolesPage() {
  const params = useParams()
  const chatId = Number(params.id)
  const router = useRouter()

  // Minimal UI — roles management without a dedicated backend endpoint for members list
  // Shows role explanations and rights matrix
  const [selectedRole, setSelectedRole] = useState<string>('admin')

  const roles = [
    { key: 'owner', label: 'Owner', desc: 'Владелец группы, все права' },
    { key: 'admin', label: 'Admin', desc: 'Полный администратор' },
    { key: 'moderator', label: 'Moderator', desc: 'Ограниченные права модерации' },
    { key: 'member', label: 'Member', desc: 'Обычный участник' },
  ]

  const currentRights = PRESET_RIGHTS[selectedRole] || []

  return (
    <div className="page">
      <div className="topbar">
        <button className="topbar-back" onClick={() => router.push(`/chat/${chatId}`)}>←</button>
        <div>
          <div className="topbar-title">Роли и права</div>
          <div className="topbar-subtitle">Матрица полномочий</div>
        </div>
      </div>

      <div className="page-content fade-in">
        {/* Role picker */}
        <div className="section">
          <div className="section-label">Роль</div>
          <div className="glass">
            {roles.map(r => (
              <div key={r.key} className="list-item" onClick={() => setSelectedRole(r.key)}
                style={{ cursor: 'pointer', background: selectedRole === r.key ? 'var(--accent-soft)' : 'transparent' }}>
                <div className="list-icon" style={{ fontSize: 20, background: selectedRole === r.key ? 'var(--accent-soft)' : 'var(--glass-bg-light)' }}>
                  {ROLE_ICONS[r.key]}
                </div>
                <div className="list-body">
                  <div className="list-title" style={{ color: selectedRole === r.key ? 'var(--accent)' : 'var(--text)' }}>{r.label}</div>
                  <div className="list-sub">{r.desc}</div>
                </div>
                <div style={{ width: 20, height: 20, borderRadius: '50%', border: `2px solid ${selectedRole === r.key ? 'var(--accent)' : 'var(--glass-border)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {selectedRole === r.key && <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--accent)' }} />}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Rights for selected role */}
        <div className="section">
          <div className="section-label">Права роли «{roles.find(r => r.key === selectedRole)?.label}»</div>
          <div className="glass">
            {RIGHTS.map(right => {
              const has = currentRights.includes(right.key)
              return (
                <div key={right.key} className="setting-row">
                  <div className="setting-info">
                    <div className="setting-title" style={{ fontSize: 13 }}>{right.label}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 16 }}>{has ? '✓' : '✕'}</span>
                    <span style={{ fontSize: 12, color: has ? 'var(--green)' : 'var(--text-3)', fontWeight: 500 }}>
                      {has ? 'Да' : 'Нет'}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Info */}
        <div className="glass-sm" style={{ padding: '14px 16px', display: 'flex', gap: 10 }}>
          <span style={{ fontSize: 18 }}>💡</span>
          <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>
            Для назначения роли откройте профиль пользователя в группе. Права автоматически применяются согласно роли в Telegram.
          </div>
        </div>
      </div>
      <ChatNav chatId={chatId} />
    </div>
  )
}


