import { useEffect, useState } from 'react'
import { decideFeedbackCase, fetchFeedbackCaseDetail, type FeedbackCaseDetail } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'

interface Props {
  caseId: string
  onClose: () => void
  onDecided: () => void
}

export function FeedbackCaseDetailPanel({ caseId, onClose, onDecided }: Props) {
  const [detail, setDetail] = useState<FeedbackCaseDetail | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchFeedbackCaseDetail(caseId)
      .then(setDetail)
      .catch(() => setError('Не удалось загрузить обращение'))
  }, [caseId])

  const decide = async (approved: boolean) => {
    setBusy(true)
    setError('')
    try {
      await decideFeedbackCase(caseId, approved)
      onDecided()
    } catch {
      setError('Не удалось принять решение')
    } finally {
      setBusy(false)
    }
  }

  if (!detail) {
    return (
      <Card className="animate-fade-in-up">
        <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
      </Card>
    )
  }

  const decided = detail.status !== 'pending'

  return (
    <Card className="animate-fade-in-up flex flex-col gap-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-semibold text-foreground">
            {detail.category_title} · {detail.case_id}
          </h2>
          <p className="text-xs text-muted">
            От {detail.submitter_display} · {detail.status}
          </p>
        </div>
        <button onClick={onClose} className="cursor-pointer text-muted hover:text-foreground">
          ×
        </button>
      </div>

      <dl className="flex flex-col gap-2 text-sm">
        {detail.fields.map((field) => (
          <div key={field.key}>
            <dt className="text-muted">{field.label}</dt>
            <dd className="whitespace-pre-wrap text-foreground">{field.value}</dd>
          </div>
        ))}
      </dl>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-2 border-t border-border pt-4">
        <Button variant="primary" onClick={() => decide(true)} disabled={busy || decided}>
          Принять
        </Button>
        <Button variant="danger" onClick={() => decide(false)} disabled={busy || decided}>
          Отклонить
        </Button>
      </div>
    </Card>
  )
}
