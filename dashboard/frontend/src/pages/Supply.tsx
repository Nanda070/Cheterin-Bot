import { Package, Plus, Trophy, XCircle } from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import { useEffect, useState } from 'react'
import {
  cancelSupply,
  closeSupply,
  createSupply,
  fetchChannels,
  fetchSupplyOverview,
  type ChannelInfo,
  type Supply,
  type SupplyOverview,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'

type Tab = 'runs' | 'settings'

function SupplyCard({
  supply,
  onClose,
  onCancel,
  busy,
  t,
}: {
  supply: Supply
  onClose?: () => void
  onCancel?: () => void
  busy?: boolean
  t: (key: string, params?: Record<string, string | number>) => string
}) {
  const isActive = supply.status === 'active'
  const statusKey = supply.status === 'active' ? 'supply.status.active' : supply.status === 'finished' ? 'supply.status.finished' : 'supply.status.cancelled'
  return (
    <Card className="animate-fade-in-up">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-foreground">
            {t('supply.card.title', { id: supply.id, opponent: supply.opponent })}
          </p>
          <p className="text-sm text-muted">
            {t('supply.card.meta', { time: supply.time_str, initiator: supply.initiator_display })} ·{' '}
            <span className={isActive ? 'text-success' : 'text-muted'}>{t(statusKey)}</span>
          </p>
        </div>
        {isActive && (
          <div className="flex shrink-0 gap-2">
            <Button variant="secondary" onClick={onClose} disabled={busy}>
              {t('supply.card.finish')}
            </Button>
            <Button variant="danger" onClick={onCancel} disabled={busy}>
              {t('supply.card.cancel')}
            </Button>
          </div>
        )}
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted">
{t('supply.card.participants', { current: supply.participants.length, limit: supply.limit })}
          </p>
          {supply.participants.length === 0 ? (
            <p className="mt-1 text-sm text-muted">—</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {supply.participants.map((p, i) => (
                <li key={p.id} className="text-sm text-foreground">
                  {i + 1}. {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
{t('supply.card.reserve', { count: supply.reserve.length })}
          {supply.reserve.length === 0 ? (
            <p className="mt-1 text-sm text-muted">—</p>
          ) : (
            <ul className="mt-1 flex flex-col gap-0.5">
              {supply.reserve.map((p, i) => (
                <li key={p.id} className="text-sm text-foreground">
                  {i + 1}. {p.display}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Card>
  )
}

export function SupplyPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('runs')
  const [overview, setOverview] = useState<SupplyOverview | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({ channel_id: '', opponent: '', limit: '10', time_str: '' })

  const reload = () => {
    fetchSupplyOverview()
      .then((data) => {
        setOverview(data)
        setError('')
      })
      .catch(() => setError(t('supply.errorLoad')))
  }

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
  }, [])

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
      await createSupply({
        channel_id: form.channel_id,
        opponent: form.opponent.trim(),
        limit: Number(form.limit),
        time_str: form.time_str.trim(),
      })
      setCreating(false)
      setForm({ channel_id: '', opponent: '', limit: '10', time_str: '' })
    })

  if (!overview) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const tabs = [
    { key: 'runs' as const, label: t('supply.tab.runs') },
    { key: 'settings' as const, label: t('supply.tab.settings') },
  ]

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex gap-1 border-b border-border">
        {tabs.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'settings' && (
        <ModuleConfigPanel variant="supply" title={t('config.section.supply')} intro={t('supply.settingsIntro')} />
      )}

      {tab === 'runs' && (
        <>
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Package size={22} className="text-primary" />
          {t('supply.title')}
        </h1>
        <Button variant="primary" onClick={() => setCreating(true)}>
          <Plus size={16} />
          {t('supply.new')}
        </Button>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="flex flex-col gap-3">
{t('supply.section.active')}
        {overview.active.length === 0 && <p className="text-sm text-muted">{t('supply.active.empty')}</p>}
        {overview.active.map((supply) => (
          <SupplyCard
            key={supply.id}
            supply={supply}
            busy={busy}
            t={t}
            onClose={() => act(() => closeSupply(supply.id))}
            onCancel={() => act(() => cancelSupply(supply.id))}
          />
        ))}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted">
          <Trophy size={16} />
          {t('supply.section.top')}
        </h2>
        {overview.stats.length === 0 && <p className="text-sm text-muted">{t('supply.stats.empty')}</p>}
        {overview.stats.length > 0 && (
          <Card>
            <ul className="flex flex-col gap-1">
              {overview.stats.map((row, i) => (
                <li key={row.user_id} className="flex justify-between text-sm">
                  <span className="text-foreground">
                    {i + 1}. {row.display}
                  </span>
                  <span className="text-muted">{row.count}</span>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted">
          <XCircle size={16} />
          {t('supply.section.history')}
        </h2>
        {overview.history.length === 0 && <p className="text-sm text-muted">{t('supply.history.empty')}</p>}
        {overview.history.map((supply) => (
          <SupplyCard key={supply.id} supply={supply} t={t} />
        ))}
      </section>

      <Modal open={creating} title={t('supply.modal.title')} onClose={() => setCreating(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="supply-channel">
              {t('supply.field.channel')}
            </label>
            <Select
              id="supply-channel"
              value={form.channel_id}
              onChange={(id) => setForm((f) => ({ ...f, channel_id: id }))}
              options={channels}
              placeholder={t('common.selectChannel')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="supply-opponent">
              {t('supply.field.opponent')}
            </label>
            <input
              id="supply-opponent"
              value={form.opponent}
              onChange={(e) => setForm((f) => ({ ...f, opponent: e.target.value }))}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="supply-limit">
                {t('supply.field.limit')}
              </label>
              <input
                id="supply-limit"
                type="number"
                min={1}
                max={99}
                value={form.limit}
                onChange={(e) => setForm((f) => ({ ...f, limit: e.target.value }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />
            </div>
            <div className="flex flex-1 flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="supply-time">
                {t('supply.field.time')}
              </label>
              <input
                id="supply-time"
                placeholder="15:10"
                value={form.time_str}
                onChange={(e) => setForm((f) => ({ ...f, time_str: e.target.value }))}
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
              disabled={busy || !form.channel_id || !form.opponent.trim() || !form.time_str.trim()}
            >
              {busy ? t('common.creating') : t('common.create')}
            </Button>
          </div>
        </div>
      </Modal>
        </>
      )}
    </div>
  )
}
