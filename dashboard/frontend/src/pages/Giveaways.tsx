import { Gift, Plus, XCircle } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  createGiveaway,
  endGiveaway,
  fetchChannels,
  fetchGiveawayOverview,
  rerollGiveaway,
  type ChannelInfo,
  type Giveaway,
  type GiveawayOverview,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { useT } from '../context/LanguageContext'

function GiveawayCard({
  giveaway,
  onEnd,
  onReroll,
  busy,
  t,
}: {
  giveaway: Giveaway
  onEnd?: () => void
  onReroll?: () => void
  busy?: boolean
  t: (key: string, params?: Record<string, string | number>) => string
}) {
  const isActive = giveaway.status === 'active'
  const statusLabel = {
    active: t('giveaways.status.active'),
    finished: t('giveaways.status.finished'),
    cancelled: t('giveaways.status.cancelled'),
  }[giveaway.status]
  const winnersLabel =
    giveaway.winners_count === 1
      ? t('giveaways.card.winners.one', { count: giveaway.winners_count })
      : t('giveaways.card.winners.other', { count: giveaway.winners_count })

  return (
    <Card className="animate-fade-in-up">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">
            №{giveaway.id} · {giveaway.prize}
          </p>
          <p className="text-sm text-muted">
            {winnersLabel} · {t('giveaways.card.initiator', { name: giveaway.initiator_display })} ·{' '}
            <span className={isActive ? 'text-success' : 'text-muted'}>{statusLabel}</span>
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          {isActive && (
            <Button variant="danger" onClick={onEnd} disabled={busy}>
              {t('giveaways.card.end')}
            </Button>
          )}
          {giveaway.status === 'finished' && (
            <Button variant="secondary" onClick={onReroll} disabled={busy}>
              {t('giveaways.card.reroll')}
            </Button>
          )}
        </div>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            {t('giveaways.card.participants', { count: giveaway.entrants.length })}
          </p>
          {giveaway.entrants.length === 0 ? (
            <p className="mt-1 text-sm text-muted">{t('common.none')}</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {giveaway.entrants.map((p, i) => (
                <li key={p.id} className="text-sm text-foreground">
                  {i + 1}. {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
            {t('giveaways.card.winnersLabel', { count: giveaway.winners.length })}
          </p>
          {giveaway.winners.length === 0 ? (
            <p className="mt-1 text-sm text-muted">{t('common.none')}</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {giveaway.winners.map((p) => (
                <li key={p.id} className="text-sm text-foreground">
                  🏆 {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Card>
  )
}

export function GiveawaysPage() {
  const t = useT()
  const [overview, setOverview] = useState<GiveawayOverview | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ channel_id: '', prize: '', duration_str: '', winners_count: '1' })

  const reload = () => {
    fetchGiveawayOverview()
      .then((data) => {
        setOverview(data)
        setError('')
      })
      .catch(() => setError(t('giveaways.errorLoad')))
  }

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
  }, [t])

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      reload()
    } catch {
      setError(t('common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  const submitCreate = () =>
    act(async () => {
      await createGiveaway({
        channel_id: form.channel_id,
        prize: form.prize.trim(),
        duration_str: form.duration_str.trim(),
        winners_count: Number(form.winners_count),
      })
      setCreating(false)
      setForm({ channel_id: '', prize: '', duration_str: '', winners_count: '1' })
    })

  if (!overview) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Gift size={22} className="text-primary" />
          {t('giveaways.title')}
        </h1>
        <Button variant="primary" onClick={() => setCreating(true)}>
          <Plus size={16} />
          {t('giveaways.new')}
        </Button>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">{t('giveaways.section.active')}</h2>
        {overview.active.length === 0 && <p className="text-sm text-muted">{t('giveaways.active.empty')}</p>}
        {overview.active.map((giveaway) => (
          <GiveawayCard
            key={giveaway.id}
            giveaway={giveaway}
            busy={busy}
            t={t}
            onEnd={() => act(() => endGiveaway(giveaway.id))}
          />
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted">
          <XCircle size={16} />
          {t('giveaways.section.history')}
        </h2>
        {overview.history.length === 0 && <p className="text-sm text-muted">{t('giveaways.history.empty')}</p>}
        {overview.history.map((giveaway) => (
          <GiveawayCard
            key={giveaway.id}
            giveaway={giveaway}
            busy={busy}
            t={t}
            onReroll={() => act(() => rerollGiveaway(giveaway.id))}
          />
        ))}
      </section>

      <Modal open={creating} title={t('giveaways.modal.title')} onClose={() => setCreating(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="giveaway-channel">
              {t('giveaways.field.channel')}
            </label>
            <Select
              id="giveaway-channel"
              value={form.channel_id}
              onChange={(id) => setForm((f) => ({ ...f, channel_id: id }))}
              options={channels}
              placeholder={t('common.selectChannel')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="giveaway-prize">
              {t('giveaways.field.prize')}
            </label>
            <input
              id="giveaway-prize"
              value={form.prize}
              onChange={(e) => setForm((f) => ({ ...f, prize: e.target.value }))}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="giveaway-duration">
                {t('giveaways.field.duration')}
              </label>
              <input
                id="giveaway-duration"
                placeholder="10m, 2h, 1d"
                value={form.duration_str}
                onChange={(e) => setForm((f) => ({ ...f, duration_str: e.target.value }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
            </div>
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="giveaway-winners">
                {t('giveaways.field.winnersCount')}
              </label>
              <input
                id="giveaway-winners"
                type="number"
                min={1}
                max={20}
                value={form.winners_count}
                onChange={(e) => setForm((f) => ({ ...f, winners_count: e.target.value }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreating(false)} disabled={busy}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              onClick={submitCreate}
              disabled={busy || !form.channel_id || !form.prize.trim() || !form.duration_str.trim()}
            >
              {busy ? t('common.creating') : t('common.create')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
