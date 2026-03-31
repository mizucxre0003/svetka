'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '@/components/Sidebar'
import { api } from '@/lib/api'

export default function TariffsPage() {
  const router = useRouter()
  const [groups, setGroups] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) { router.push('/login'); return }
    api.groups({limit:'200'}).then((d:any)=>setGroups(d.items)).catch(()=>router.push('/login')).finally(()=>setLoading(false))
  }, [router])

  const free = groups.filter(g=>g.tariff==='free').length
  const trial = groups.filter(g=>g.tariff==='trial').length
  const pro = groups.filter(g=>g.tariff==='pro').length

  const TB: Record<string,string> = {free:'badge-gray',trial:'badge-yellow',pro:'badge-accent'}
  const SB: Record<string,string> = {active:'badge-green',blocked:'badge-red',inactive:'badge-yellow'}

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Тарифы</h1>
          <p className="page-subtitle">Управление планами</p>
        </div>
        <div className="grid-3" style={{marginBottom:24}}>
          {[['Free',free,'badge-gray'],['Trial',trial,'badge-yellow'],['Pro',pro,'badge-accent']].map(([l,c,b])=>(
            <div key={String(l)} className="card">
              <span className={`badge ${b}`}>{l}</span>
              <div className="card-value" style={{marginTop:8}}>{c}</div>
            </div>
          ))}
        </div>
        <div className="card" style={{padding:0}}>
          <div className="table-wrap">
            {loading ? <div className="loading">Загрузка...</div> : (
              <table>
                <thead><tr><th>Группа</th><th>Тариф</th><th>Статус</th><th>Участников</th><th>Активность</th><th></th></tr></thead>
                <tbody>
                  {groups.map((g:any)=>(
                    <tr key={g.id}>
                      <td style={{fontWeight:500}}>{g.title}</td>
                      <td><span className={`badge ${TB[g.tariff]||'badge-gray'}`}>{g.tariff}</span></td>
                      <td><span className={`badge ${SB[g.status]||'badge-gray'}`}>{g.status}</span></td>
                      <td>{g.member_count?.toLocaleString()}</td>
                      <td style={{color:'var(--text-secondary)',fontSize:12}}>{g.last_activity_at?new Date(g.last_activity_at).toLocaleDateString('ru-RU'):'—'}</td>
                      <td><Link href={`/groups/${g.id}`} className="btn btn-secondary btn-sm">→</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
