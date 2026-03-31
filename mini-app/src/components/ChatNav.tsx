'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const TABS = [
  { href: '', icon: '▦', label: 'Главная' },
  { href: '/moderation', icon: '🛡', label: 'Модерация' },
  { href: '/protection', icon: '⚡', label: 'Защита' },
  { href: '/messages', icon: '✉', label: 'Контент' },
  { href: '/stats', icon: '◈', label: 'Статы' },
]

export default function ChatNav({ chatId }: { chatId: number }) {
  const path = usePathname()
  const base = `/chat/${chatId}`

  return (
    <nav className="bottom-nav">
      {TABS.map(t => {
        const href = base + t.href
        const active = t.href === '' ? path === base : path.startsWith(href)
        return (
          <Link key={t.href} href={href} className={`nav-btn${active ? ' active' : ''}`}>
            <span className="nav-icon">{t.icon}</span>
            {t.label}
          </Link>
        )
      })}
    </nav>
  )
}
