import { ClipboardText } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchAudit, type AuditPage } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

const METHOD_COLOR: Record<string, string> = {
  POST: 'text-success',
  PUT: 'text-warning',
  PATCH: 'text-warning',
  DELETE: 'text-danger',
}

export function AuditPage() {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<AuditPage | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchAudit(page)
      .then(setData)
      .catch(() => setError('Не удалось загрузить журнал аудита'))
  }, [page])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ClipboardText size={22} className="text-primary" />
          Аудит дашборда
        </h1>
        <p className="mt-1 text-sm text-muted">
          Все изменения, сделанные модераторами через панель. Записей: {data?.total ?? '…'}
        </p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {!data && !error && <p className="text-sm text-muted">Загрузка…</p>}

      {data && data.entries.length === 0 && (
        <Card>
          <p className="text-sm text-muted">Журнал пуст — действий через дашборд ещё не было.</p>
        </Card>
      )}

      {data && data.entries.length > 0 && (
        <Card className="p-0">
          {data.entries.map((entry, i) => (
            <div key={i} className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border px-4 py-2.5 last:border-b-0">
              <span className={`w-14 text-xs font-semibold ${METHOD_COLOR[entry.method] ?? 'text-muted'}`}>
                {entry.method}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm text-foreground">{entry.action}</p>
                <p className="truncate text-xs text-muted">{entry.path}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-foreground">{entry.moderator_name}</p>
                <p className="text-xs text-muted">{new Date(entry.ts * 1000).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </Card>
      )}

      {data && totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button variant="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            ← Назад
          </Button>
          <span className="text-sm text-muted">
            Стр. {page} из {totalPages}
          </span>
          <Button variant="ghost" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Вперёд →
          </Button>
        </div>
      )}
    </div>
  )
}
