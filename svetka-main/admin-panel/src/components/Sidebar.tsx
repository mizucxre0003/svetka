'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'

const NAV = [
  { href: '/dashboard', icon: '▦', label: 'Dashboard' },
  { href: '/groups', icon: '◉', label: 'Группы' },
  { href: '/analytics', icon: '◈', label: 'Analytics' },
  { href: '/funnel', icon: '▽', label: 'Funnel' },
  { href: '/tariffs', icon: '◆', label: 'Тарифы' },
  { href: '/logs', icon: '≡', label: 'System Logs' },
]

export default function Sidebar() {
  const path = usePathname()
  const router = useRouter()

  function handleLogout() {
    localStorage.removeItem('admin_token')
    router.push('/login')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">✦</div>
        <div>
          <span className="logo-text">Svetka</span>
          <span className="logo-badge">ADMIN</span>
        </div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section-label">Навигация</div>
        {NAV.map(item => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item${path.startsWith(item.href) ? ' active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button className="nav-item" onClick={handleLogout} style={{ width: '100%' }}>
          <span className="nav-icon">⊗</span>
          Выйти
        </button>
      </div>
    </aside>
  )
}
