import { useEffect, useState } from 'react'
import { fetchFeedbackCases, type FeedbackCaseSummary } from '../api/client'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { FeedbackCaseDetailPanel } from './FeedbackCaseDetailPanel'

type StatusFilter = 'pending' | 'approved' | 'denied' | 'all'

export function FeedbackCasesPage() {
  const [status, setStatus] = useState<StatusFilter>('pending')
  const [cases, setCases] = useState<FeedbackCaseSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')

  const reload = () => {
    fetchFeedbackCases(status === 'all' ? undefined : status)
      .then(setCases)
      .catch(() => setError('Не удалось загрузить обращения'))
  }

  useEffect(reload, [status])

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">Обращения</h1>
          <label className="ml-auto text-sm text-muted" htmlFor="feedback-status">
            Статус
          </label>
          <Select
            id="feedback-status"
            value={status}
            onChange={(id) => setStatus(id as StatusFilter)}
            options={[
              { id: 'pending', name: 'На рассмотрении' },
              { id: 'approved', name: 'Принято' },
              { id: 'denied', name: 'Отклонено' },
              { id: 'all', name: 'Все' },
            ]}
            className="w-52"
          />
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {cases.map((c) => (
            <Card key={c.case_id} interactive className="!p-3" onClick={() => setSelectedId(c.case_id)}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground">
                    {c.category_title} · {c.case_id}
                  </p>
                  <p className="text-xs text-muted">
                    {c.submitter_display} · {c.status}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {cases.length === 0 && <p className="text-sm text-muted">Обращений нет.</p>}
        </div>
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <FeedbackCaseDetailPanel
            caseId={selectedId}
            onClose={() => setSelectedId(null)}
            onDecided={() => {
              setSelectedId(null)
              reload()
            }}
          />
        </div>
      )}
    </div>
  )
}
