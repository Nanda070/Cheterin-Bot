import { Gear, Plus, ShieldWarning, Trash } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  createEscalationRule,
  deleteEscalationRule,
  fetchAutomod,
  fetchChannels,
  updateAutomodEnabled,
  updateAutomodFilter,
  updateManualWarnDuration,
  type AutomodFilter,
  type AutomodPunishment,
  type AutomodSettings,
  type ChannelInfo,
  type EscalationAction,
  type EscalationRule,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { formatDurationOrPermanent } from '../utils/formatDuration'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function automodFilterLabel(filterKey: string, t: ReturnType<typeof useT>): string {
  return t(`automod.filters.${filterKey}.label`)
}

function automodFilterDescription(filterKey: string, t: ReturnType<typeof useT>): string {
  return t(`automod.filters.${filterKey}.description`)
}

function minutesToParts(total: number) {
  const days = Math.floor(total / 1440)
  const hours = Math.floor((total % 1440) / 60)
  const minutes = total % 60
  return { days, hours, minutes }
}

function partsToMinutes(days: number, hours: number, minutes: number) {
  return days * 1440 + hours * 60 + minutes
}

function DurationInputs({ minutes, onChange }: { minutes: number; onChange: (m: number) => void }) {
  const t = useT()
  const parts = minutesToParts(minutes)
  return (
    <div className="flex gap-2">
      <div className="flex flex-1 flex-col gap-1">
        <label className="text-xs text-muted">{t('automod.duration.daysLabel')}</label>
        <input
          type="number"
          min={0}
          value={parts.days}
          onChange={(e) => onChange(partsToMinutes(Number(e.target.value) || 0, parts.hours, parts.minutes))}
          className={inputClass}
        />
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <label className="text-xs text-muted">{t('automod.duration.hoursLabel')}</label>
        <input
          type="number"
          min={0}
          max={23}
          value={parts.hours}
          onChange={(e) => onChange(partsToMinutes(parts.days, Number(e.target.value) || 0, parts.minutes))}
          className={inputClass}
        />
      </div>
      <div className="flex flex-1 flex-col gap-1">
        <label className="text-xs text-muted">{t('automod.duration.minutesLabel')}</label>
        <input
          type="number"
          min={0}
          max={59}
          value={parts.minutes}
          onChange={(e) => onChange(partsToMinutes(parts.days, parts.hours, Number(e.target.value) || 0))}
          className={inputClass}
        />
      </div>
    </div>
  )
}

function FilterExtraFields({
  filterKey,
  draft,
  setDraft,
}: {
  filterKey: string
  draft: AutomodFilter
  setDraft: (patch: Partial<AutomodFilter>) => void
}) {
  const t = useT()

  const listInput = (value: string[] | undefined, key: 'whitelist_domains' | 'blocklist_keywords' | 'words', label: string) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-muted">{label}</label>
      <input
        defaultValue={(value ?? []).join(', ')}
        onBlur={(e) =>
          setDraft({ [key]: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) } as Partial<AutomodFilter>)
        }
        className={inputClass}
      />
    </div>
  )

  switch (filterKey) {
    case 'links':
      return listInput(draft.whitelist_domains, 'whitelist_domains', t('automod.filter.whitelistDomains'))
    case 'invites':
      return (
        <Toggle
          checked={!!draft.allow_own_server}
          onChange={(v) => setDraft({ allow_own_server: v })}
          label={t('automod.filter.allowOwnServer')}
        />
      )
    case 'scam_links':
      return listInput(draft.blocklist_keywords, 'blocklist_keywords', t('automod.filter.blocklistKeywords'))
    case 'bad_words':
      return listInput(draft.words, 'words', t('automod.filter.badWords'))
    case 'repeated_text':
      return (
        <>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('automod.filter.maxRepeats')}</label>
            <input
              type="number"
              min={1}
              value={draft.max_repeats ?? 4}
              onChange={(e) => setDraft({ max_repeats: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <Toggle
            checked={!!draft.consecutive_only}
            onChange={(v) => setDraft({ consecutive_only: v })}
            label={t('automod.filter.consecutiveOnly')}
          />
          <Toggle
            checked={!!draft.reset_on_trigger}
            onChange={(v) => setDraft({ reset_on_trigger: v })}
            label={t('automod.filter.resetOnTrigger')}
          />
        </>
      )
    case 'caps_lock':
      return (
        <div className="flex gap-2">
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted">{t('automod.filter.maxCapsPercent')}</label>
            <input
              type="number"
              min={1}
              max={100}
              value={draft.max_percent ?? 70}
              onChange={(e) => setDraft({ max_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-1 flex-col gap-1">
            <label className="text-xs text-muted">{t('automod.filter.minLength')}</label>
            <input
              type="number"
              min={0}
              value={draft.min_length ?? 10}
              onChange={(e) => setDraft({ min_length: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      )
    case 'emoji_spam':
    case 'mentions':
    case 'zalgo': {
      const label =
        filterKey === 'emoji_spam'
          ? t('automod.filter.maxEmoji')
          : filterKey === 'mentions'
            ? t('automod.filter.maxMentions')
            : t('automod.filter.maxZalgo')
      return (
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{label}</label>
          <input
            type="number"
            min={1}
            value={draft.max_count ?? 5}
            onChange={(e) => setDraft({ max_count: Number(e.target.value) })}
            className={inputClass}
          />
        </div>
      )
    }
    default:
      return null
  }
}

function FilterModal({
  filterKey,
  filter,
  channels,
  onClose,
  onSaved,
}: {
  filterKey: string
  filter: AutomodFilter
  channels: ChannelInfo[]
  onClose: () => void
  onSaved: () => void
}) {
  const t = useT()
  const [draft, setDraftState] = useState<AutomodFilter>(filter)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const punishmentOptions = useMemo(
    () =>
      (['none', 'warn', 'mute', 'kick', 'ban'] as AutomodPunishment[]).map((id) => ({
        id,
        name: t(`automod.punishment.${id}`),
      })),
    [t],
  )

  const setDraft = (patch: Partial<AutomodFilter>) => setDraftState((prev) => ({ ...prev, ...patch }))

  const save = async () => {
    setBusy(true)
    setError('')
    try {
      await updateAutomodFilter(filterKey, draft)
      onSaved()
      onClose()
    } catch (err) {
      setError(formatApiError(err, t, 'automod.errorSaveFilter'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open title={automodFilterLabel(filterKey, t)} onClose={onClose}>
      <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto pr-1">
        <Toggle checked={draft.delete_message} onChange={(v) => setDraft({ delete_message: v })} label={t('automod.filter.deleteMessage')} />

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{t('automod.filter.punishment')}</label>
          <Select
            value={draft.punishment}
            onChange={(id) => setDraft({ punishment: id as AutomodPunishment })}
            options={punishmentOptions}
          />
        </div>

        {draft.punishment !== 'none' && draft.punishment !== 'kick' && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">
              {draft.punishment === 'warn' ? t('automod.filter.warnDuration') : t('automod.filter.punishmentDuration')}
            </label>
            <DurationInputs minutes={draft.duration_minutes} onChange={(m) => setDraft({ duration_minutes: m })} />
          </div>
        )}

        <FilterExtraFields filterKey={filterKey} draft={draft} setDraft={setDraft} />

        <div className="border-t border-border pt-3">
          <Toggle checked={draft.notify_member} onChange={(v) => setDraft({ notify_member: v })} label={t('automod.filter.notifyMember')} />
        </div>

        {draft.notify_member && (
          <>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">{t('automod.filter.notifyChannel')}</label>
              <Select
                value={draft.notify_channel_id}
                onChange={(id) => setDraft({ notify_channel_id: id })}
                options={channels}
                placeholder={t('automod.filter.currentChannel')}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted">{t('automod.filter.notifyTemplate')}</label>
              <textarea
                rows={3}
                value={draft.notify_template}
                onChange={(e) => setDraft({ notify_template: e.target.value })}
                className={inputClass}
              />
            </div>
          </>
        )}

        {error && <p className="text-sm text-danger">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            {t('common.cancel')}
          </Button>
          <Button variant="primary" onClick={save} disabled={busy}>
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

function FilterCard({
  filterKey,
  filter,
  onToggle,
  onOpenSettings,
}: {
  filterKey: string
  filter: AutomodFilter
  onToggle: (v: boolean) => void
  onOpenSettings: () => void
}) {
  const t = useT()
  const label = automodFilterLabel(filterKey, t)
  const description = automodFilterDescription(filterKey, t)

  return (
    <Card className="flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-foreground">{label}</p>
          <p className="text-xs text-muted">{description}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Toggle checked={filter.enabled} onChange={onToggle} />
          <button
            type="button"
            onClick={onOpenSettings}
            aria-label={t('automod.filter.settingsAria', { label })}
            className="cursor-pointer text-muted transition-colors hover:text-foreground"
          >
            <Gear size={18} />
          </button>
        </div>
      </div>
    </Card>
  )
}

function EscalationSection({
  escalation,
  busy,
  onCreate,
  onDelete,
}: {
  escalation: EscalationRule[]
  busy: boolean
  onCreate: (input: { count: number; action: EscalationAction; duration_minutes: number }) => Promise<unknown>
  onDelete: (id: string) => Promise<unknown>
}) {
  const t = useT()
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({ count: '3', action: 'mute' as EscalationAction, duration_minutes: 1440 })

  const escalationActionOptions = useMemo(
    () =>
      (['mute', 'kick', 'ban'] as EscalationAction[]).map((id) => ({
        id,
        name: t(`automod.punishment.${id}`),
      })),
    [t],
  )

  const submit = async () => {
    await onCreate({ count: Number(form.count), action: form.action, duration_minutes: form.duration_minutes })
    setAdding(false)
    setForm({ count: '3', action: 'mute', duration_minutes: 1440 })
  }

  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">{t('automod.escalation.title')}</h2>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={15} />
          {t('automod.escalation.addThreshold')}
        </Button>
      </div>

      {escalation.length === 0 && (
        <p className="text-sm text-muted">{t('automod.escalation.empty')}</p>
      )}

      {escalation
        .slice()
        .sort((a, b) => a.count - b.count)
        .map((rule) => (
          <div key={rule.id} className="flex items-center justify-between gap-3 border-b border-border pb-2 last:border-b-0">
            <p className="text-sm text-foreground">
              {t('automod.escalation.rule', {
                count: rule.count,
                suffix: rule.count === 1 ? t('automod.escalation.suffixOne') : t('automod.escalation.suffixMany'),
                action: t(`automod.punishment.${rule.action}`),
                duration: formatDurationOrPermanent(rule.duration_minutes, t),
              })}
            </p>
            <button
              type="button"
              onClick={() => onDelete(rule.id)}
              disabled={busy}
              aria-label={t('automod.escalation.deleteAria', { count: rule.count })}
              className="cursor-pointer text-muted transition-colors hover:text-danger"
            >
              <Trash size={16} />
            </button>
          </div>
        ))}

      <Modal open={adding} title={t('automod.escalation.modalTitle')} onClose={() => setAdding(false)}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="escalation-count">
              {t('automod.escalation.warnCount')}
            </label>
            <input
              id="escalation-count"
              type="number"
              min={1}
              value={form.count}
              onChange={(e) => setForm((f) => ({ ...f, count: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">{t('automod.escalation.action')}</label>
            <Select
              value={form.action}
              onChange={(id) => setForm((f) => ({ ...f, action: id as EscalationAction }))}
              options={escalationActionOptions}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">{t('automod.escalation.duration')}</label>
            <DurationInputs minutes={form.duration_minutes} onChange={(m) => setForm((f) => ({ ...f, duration_minutes: m }))} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={submit} disabled={!form.count}>
              {t('common.add')}
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}

export function AutoModPage() {
  const t = useT()
  const [settings, setSettings] = useState<AutomodSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [manualWarnDuration, setManualWarnDuration] = useState(0)

  const reload = () =>
    fetchAutomod()
      .then((data) => {
        setSettings(data)
        setManualWarnDuration(data.manual_warn_duration_minutes)
        setError('')
      })
      .catch(() => setError(t('automod.errorLoad')))

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
      await reload()
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <ShieldWarning size={22} className="text-primary" />
            {t('automod.title')}
          </h1>
          <p className="mt-1 text-sm text-muted">{t('automod.intro')}</p>
        </div>
        <Toggle checked={settings.enabled} onChange={(v) => act(() => updateAutomodEnabled(v))} label={t('automod.enabled')} disabled={busy} />
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(settings.filters).map(([key, filter]) => (
          <FilterCard
            key={key}
            filterKey={key}
            filter={filter}
            onToggle={(v) => act(() => updateAutomodFilter(key, { enabled: v }))}
            onOpenSettings={() => setEditingKey(key)}
          />
        ))}
      </div>

      <EscalationSection
        escalation={settings.escalation}
        busy={busy}
        onCreate={(input) => act(() => createEscalationRule(input))}
        onDelete={(id) => act(() => deleteEscalationRule(id))}
      />

      <Card className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">{t('automod.manualWarn.title')}</h2>
        <p className="text-sm text-muted">{t('automod.manualWarn.intro')}</p>
        <DurationInputs minutes={manualWarnDuration} onChange={setManualWarnDuration} />
        <div>
          <Button variant="primary" onClick={() => act(() => updateManualWarnDuration(manualWarnDuration))} disabled={busy}>
            {t('common.save')}
          </Button>
        </div>
      </Card>

      {editingKey && (
        <FilterModal
          filterKey={editingKey}
          filter={settings.filters[editingKey]}
          channels={channels}
          onClose={() => setEditingKey(null)}
          onSaved={reload}
        />
      )}
    </div>
  )
}
