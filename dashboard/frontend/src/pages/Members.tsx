import { MagnifyingGlass } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchMembers, type MembersPage as MembersPageData } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { MemberDetailPanel } from './MemberDetailPanel'

export function MembersPage() {
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<MembersPageData | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebounced(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    let cancelled = false
    fetchMembers(debounced, page)
      .then((result) => {
        if (cancelled) return
        setData(result)
        setError('')
      })
      .catch(() => {
        if (!cancelled) setError('Не удалось загрузить участников')
      })
    return () => {
      cancelled = true
    }
  }, [debounced, page])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="relative mb-4 max-w-md">
          <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по имени или нику…"
            className="w-full rounded-control border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
          />
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {data?.members.map((member) => (
            <Card
              key={member.id}
              interactive
              className="!p-3"
              onClick={() => setSelectedId(member.id)}
            >
              <div className="flex items-center gap-3">
                {member.avatar ? (
                  <img src={member.avatar} alt="" className="h-9 w-9 rounded-full" />
                ) : (
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                    {member.username.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <div className="flex-1">
                  <p className="text-sm text-foreground">{member.username}</p>
                  <p className="text-xs text-muted">
                    {member.display_name}
                    {member.is_bot && ' · бот'} · ролей: {member.role_count}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {data && data.members.length === 0 && (
            <p className="text-sm text-muted">Никого не найдено.</p>
          )}
        </div>

        {data && totalPages > 1 && (
          <div className="mt-4 flex items-center gap-3">
            <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Назад
            </Button>
            <span className="text-sm text-muted">
              {page} / {totalPages}
            </span>
            <Button
              variant="secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Вперёд
            </Button>
          </div>
        )}
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <MemberDetailPanel
            memberId={selectedId}
            onClose={() => setSelectedId(null)}
            onActionDone={() => fetchMembers(debounced, page).then(setData).catch(() => {})}
          />
        </div>
      )}
    </div>
  )
}
