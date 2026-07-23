import { ChartBar, Stop } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { endPoll, fetchPolls, type PollEntry } from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

export function PollsPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [polls, setPolls] = useState<PollEntry[] | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = () =>
    fetchPolls()
      .then((data) => {
        setPolls(data.polls)
        setError('')
      })
      .catch((err) => setError(formatApiError(err, t, 'polls.errorLoad')))

  useEffect(() => {
    reload()
  }, [t])

  const stop = async (id: number) => {
    setBusy(true)
    setError('')
    try {
      await endPoll(id)
      await reload()
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (!polls) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        {embedded ? (
          <h2 className="flex items-center gap-2 font-semibold text-foreground">
            <ChartBar size={20} className="text-primary" />
            {t('polls.title')}
          </h2>
        ) : (
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <ChartBar size={22} className="text-primary" />
            {t('polls.title')}
          </h1>
        )}
        <p className="mt-1 text-sm text-muted">{t('polls.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      {polls.length === 0 ? (
        <Card>
          <p className="text-sm text-muted">{t('polls.empty')}</p>
        </Card>
      ) : (
        polls.map((poll) => (
          <Card key={poll.id} className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-foreground">{poll.question}</p>
                <p className="text-xs text-muted">
                  {poll.ended ? t('polls.ended') : t('polls.ends', { at: poll.ends_at })} ·{' '}
                  {t('polls.votes', { count: poll.total_votes })}
                </p>
              </div>
              {!poll.ended && (
                <Button variant="secondary" disabled={busy} onClick={() => stop(poll.id)}>
                  <Stop size={15} />
                  {t('polls.end')}
                </Button>
              )}
            </div>
            <ul className="flex flex-col gap-1.5">
              {poll.options.map((opt, i) => (
                <li key={`${poll.id}-${i}`} className="flex justify-between text-sm text-foreground">
                  <span>{opt}</span>
                  <span className="text-muted">{poll.tallies[i] ?? 0}</span>
                </li>
              ))}
            </ul>
          </Card>
        ))
      )}
    </div>
  )
}
