import { useEffect, useState } from 'react'
import { useT } from '../context/LanguageContext'
import { useNavigate } from 'react-router-dom'
import {
  createBracket,
  fetchBrackets,
  fetchEventEntries,
  fetchEvents,
  type BracketFormat,
  type BracketSummary,
  type EventSummary,
} from '../api/client'

const FORMAT_KEYS: Record<BracketFormat, string> = {
  single_elim: 'brackets.format.singleElim',
  double_elim: 'brackets.format.doubleElim',
  round_robin: 'brackets.format.roundRobin',
}
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'

type SourceTab = 'event' | 'manual'

function shuffle(items: string[]): string[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

export function BracketsPage() {
  const t = useT()
  const navigate = useNavigate()
  const [brackets, setBrackets] = useState<BracketSummary[]>([])
  const [events, setEvents] = useState<EventSummary[]>([])
  const [error, setError] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [tab, setTab] = useState<SourceTab>('event')
  const [selectedEventId, setSelectedEventId] = useState('')
  const [manualText, setManualText] = useState('')
  const [title, setTitle] = useState('')
  const [entries, setEntries] = useState<string[]>([])
  const [step, setStep] = useState<'source' | 'seed'>('source')
  const [format, setFormat] = useState<BracketFormat>('single_elim')
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)

  const reload = () => {
    fetchBrackets()
      .then(setBrackets)
      .catch(() => setError(t('brackets.errorLoad')))
  }

  useEffect(reload, [])
  useEffect(() => {
    Promise.all([fetchEvents('open'), fetchEvents('closed')])
      .then(([open, closed]) => setEvents([...open, ...closed]))
      .catch(() => {})
  }, [])

  const openCreate = () => {
    setTab('event')
    setSelectedEventId('')
    setManualText('')
    setTitle('')
    setEntries([])
    setStep('source')
    setCreateError('')
    setCreateOpen(true)
  }

  const loadEventEntries = async (eventId: string) => {
    setSelectedEventId(eventId)
    if (!eventId) {
      setEntries([])
      return
    }
    try {
      const loaded = await fetchEventEntries(eventId)
      setEntries(loaded)
    } catch {
      setCreateError(t('brackets.errorEntries'))
    }
  }

  const goToSeedStep = () => {
    if (tab === 'manual') {
      const lines = manualText
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)
      setEntries(lines)
    }
    setStep('seed')
  }

  const moveEntry = (index: number, direction: -1 | 1) => {
    setEntries((prev) => {
      const target = index + direction
      if (target < 0 || target >= prev.length) return prev
      const copy = [...prev]
      ;[copy[index], copy[target]] = [copy[target], copy[index]]
      return copy
    })
  }

  const save = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      await createBracket(title, entries, tab === 'event' ? selectedEventId || null : null, format)
      setCreateOpen(false)
      reload()
    } catch {
      setCreateError(t('brackets.errorCreate'))
    } finally {
      setCreateBusy(false)
    }
  }

  return (
    <div>
      <div className="mb-4 flex items-center gap-3">
        <h1 className="text-lg font-semibold text-foreground">{t('brackets.title')}</h1>
        <Button variant="primary" onClick={openCreate} className="ml-auto">
          {t('brackets.create')}
        </Button>
      </div>

      {error && <p className="mb-4 text-sm text-danger">{error}</p>}

      <div className="flex flex-col gap-2">
        {brackets.map((b) => (
          <Card key={b.id} interactive className="!p-3" onClick={() => navigate(`/brackets/${b.id}`)}>
            <p className="text-sm text-foreground">{b.title}</p>
            <p className="text-xs text-muted">
              {t('brackets.entryCount', { count: b.entry_count })} · {t(FORMAT_KEYS[b.format])}
            </p>
          </Card>
        ))}
        {brackets.length === 0 && <p className="text-sm text-muted">{t('brackets.empty')}</p>}
      </div>

      <Modal open={createOpen} title={t('brackets.modal.create')} onClose={() => setCreateOpen(false)}>
        {step === 'source' ? (
          <div className="flex flex-col gap-3">
            <div className="flex gap-2">
              <Button variant={tab === 'event' ? 'primary' : 'secondary'} onClick={() => setTab('event')}>
                {t('brackets.source.event')}
              </Button>
              <Button variant={tab === 'manual' ? 'primary' : 'secondary'} onClick={() => setTab('manual')}>
                {t('brackets.source.manual')}
              </Button>
            </div>

            {tab === 'event' ? (
              <>
                <label className="text-sm text-muted" htmlFor="bracket-event">
                  {t('brackets.field.event')}
                </label>
                <Select
                  id="bracket-event"
                  value={selectedEventId}
                  onChange={(id) => loadEventEntries(id)}
                  options={events
                    .filter((ev) => ev.type === 'tournament')
                    .map((ev) => ({ id: ev.message_id, name: ev.title }))}
                  placeholder={t('brackets.field.event')}
                />
                {entries.length > 0 && (
                  <p className="text-xs text-muted">{t('brackets.entriesLoaded', { count: entries.length })}</p>
                )}
              </>
            ) : (
              <>
                <label className="text-sm text-muted" htmlFor="bracket-manual-names">
                  {t('brackets.field.names')}
                </label>
                <textarea
                  id="bracket-manual-names"
                  value={manualText}
                  onChange={(e) => setManualText(e.target.value)}
                  rows={6}
                  className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                />
              </>
            )}

            <label className="text-sm text-muted" htmlFor="bracket-title">
              {t('brackets.field.title')}
            </label>
            <input
              id="bracket-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />

            <label className="text-sm text-muted" htmlFor="bracket-format">
              {t('brackets.field.format')}
            </label>
            <Select
              id="bracket-format"
              value={format}
              onChange={(id) => setFormat(id as BracketFormat)}
              options={(Object.keys(FORMAT_KEYS) as BracketFormat[]).map((f) => ({ id: f, name: t(FORMAT_KEYS[f]) }))}
            />
            <p className="text-xs text-muted">
              {format === 'single_elim' && t('brackets.format.singleElimHint')}
              {format === 'double_elim' && t('brackets.format.doubleElimHint')}
              {format === 'round_robin' && t('brackets.format.roundRobinHint')}
            </p>

            {createError && <p className="text-sm text-danger">{createError}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setCreateOpen(false)}>
                {t('common.cancel')}
              </Button>
              <Button variant="primary" onClick={goToSeedStep}>
                {t('common.next')}
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted">{t('brackets.seedOrder')}</p>
              <Button variant="secondary" onClick={() => setEntries((prev) => shuffle(prev))}>
                {t('brackets.shuffle')}
              </Button>
            </div>

            <ul className="flex flex-col gap-1">
              {entries.map((entry, index) => (
                <li
                  key={`${entry}-${index}`}
                  className="flex items-center justify-between rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
                >
                  <span>{entry}</span>
                  <span className="flex gap-1">
                    <button
                      type="button"
                      aria-label={t('brackets.moveUp')}
                      onClick={() => moveEntry(index, -1)}
                      className="cursor-pointer text-muted hover:text-foreground"
                    >
                      ↑
                    </button>
                    <button
                      type="button"
                      aria-label={t('brackets.moveDown')}
                      onClick={() => moveEntry(index, 1)}
                      className="cursor-pointer text-muted hover:text-foreground"
                    >
                      ↓
                    </button>
                  </span>
                </li>
              ))}
            </ul>

            {createError && <p className="text-sm text-danger">{createError}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setStep('source')} disabled={createBusy}>
                {t('common.back')}
              </Button>
              <Button variant="primary" onClick={save} disabled={createBusy || entries.length < 2}>
                {createBusy ? t('common.creating') : t('common.generate')}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
