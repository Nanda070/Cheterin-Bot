import { Timer, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { deleteTimedRole, fetchTimedRoles, type TimedRoleEntry } from '../api/client'
import { formatApiError } from '../api/errors'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

export function TimedRolesPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [rows, setRows] = useState<TimedRoleEntry[] | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = () =>
    fetchTimedRoles()
      .then((data) => {
        setRows(data.timed_roles)
        setError('')
      })
      .catch((err) => setError(formatApiError(err, t, 'timedRoles.errorLoad')))

  useEffect(() => {
    reload()
  }, [t])

  const remove = async (id: number) => {
    setBusy(true)
    setError('')
    try {
      await deleteTimedRole(id)
      await reload()
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (!rows) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        {embedded ? (
          <h2 className="flex items-center gap-2 font-semibold text-foreground">
            <Timer size={20} className="text-primary" />
            {t('timedRoles.title')}
          </h2>
        ) : (
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <Timer size={22} className="text-primary" />
            {t('timedRoles.title')}
          </h1>
        )}
        <p className="mt-1 text-sm text-muted">{t('timedRoles.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {rows.length === 0 ? (
        <Card>
          <p className="text-sm text-muted">{t('timedRoles.empty')}</p>
        </Card>
      ) : (
        rows.map((row) => (
          <Card key={row.id} className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">
                {row.display_name} · {row.role_name}
              </p>
              <p className="text-xs text-muted">{t('timedRoles.expires', { at: row.expires_at })}</p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => remove(row.id)}
              className="text-muted hover:text-danger"
              aria-label={t('common.delete')}
            >
              <Trash size={17} />
            </button>
          </Card>
        ))
      )}
    </div>
  )
}
