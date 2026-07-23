import { MagnifyingGlass, Timer, UsersThree } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchMembers, type MembersPage as MembersPageData } from '../api/client'
import { MassAssignModal } from '../components/MassAssignModal'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'
import { MemberDetailPanel } from './MemberDetailPanel'
import { TimedRolesPage } from './TimedRoles'

type Tab = 'list' | 'timedRoles'

function parseMembersTab(raw: string | null): Tab {
  return raw === 'timedRoles' ? 'timedRoles' : 'list'
}

export function MembersPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = parseMembersTab(searchParams.get('tab'))
  const setTab = (next: Tab) => {
    if (next === 'list') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [page, setPage] = useState(1)
  const [data, setData] = useState<MembersPageData | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [massAssignOpen, setMassAssignOpen] = useState(false)

  const tabs = useMemo(
    () =>
      [
        { key: 'list' as const, label: t('members.tab.list'), icon: UsersThree },
        { key: 'timedRoles' as const, label: t('members.tab.timedRoles'), icon: Timer },
      ] as const,
    [t],
  )

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebounced(search)
      setPage(1)
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    if (tab !== 'list') return
    let cancelled = false
    fetchMembers(debounced, page)
      .then((result) => {
        if (cancelled) return
        setData(result)
        setError('')
      })
      .catch(() => {
        if (!cancelled) setError(t('members.errorLoad'))
      })
    return () => {
      cancelled = true
    }
  }, [debounced, page, t, tab])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-1 border-b border-border pb-1">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setTab(key)
              setSelectedId(null)
              setError('')
            }}
            className={`flex cursor-pointer items-center gap-1.5 rounded-control px-3 py-1.5 text-sm transition-colors ${
              tab === key ? 'bg-primary-muted text-foreground' : 'text-muted hover:text-foreground'
            }`}
          >
            <Icon size={16} weight={tab === key ? 'fill' : 'regular'} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'timedRoles' && <TimedRolesPage embedded />}

      {tab === 'list' && (
        <div className="flex gap-6">
          <div className="flex-1">
            <div className="mb-4 flex items-center gap-3">
              <div className="relative max-w-md flex-1">
                <MagnifyingGlass size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={t('members.searchPlaceholder')}
                  className="w-full rounded-control border border-border bg-surface py-2 pl-9 pr-3 text-sm text-foreground outline-none focus:border-primary"
                />
              </div>
              <Button variant="secondary" onClick={() => setMassAssignOpen(true)}>
                {t('members.massAssign')}
              </Button>
            </div>

            <MassAssignModal
              open={massAssignOpen}
              onClose={() => {
                setMassAssignOpen(false)
                fetchMembers(debounced, page).then(setData).catch(() => {})
              }}
            />

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
                        {member.is_bot && ` · ${t('members.bot')}`} ·{' '}
                        {t('members.rolesCount', { count: member.role_count })}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
              {data && data.members.length === 0 && (
                <p className="text-sm text-muted">{t('members.empty')}</p>
              )}
            </div>

            {data && totalPages > 1 && (
              <div className="mt-4 flex items-center gap-3">
                <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  {t('common.back')}
                </Button>
                <span className="text-sm text-muted">
                  {t('members.page', { page, total: totalPages })}
                </span>
                <Button
                  variant="secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  {t('common.forward')}
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
      )}
    </div>
  )
}
