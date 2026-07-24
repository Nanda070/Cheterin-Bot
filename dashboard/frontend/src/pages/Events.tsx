import { CalendarCheck, ChartBar, Gift, Trophy } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import {
  createEvent,
  fetchChannels,
  fetchEvents,
  fetchRoles,
  type ChannelInfo,
  type CreateEventSpec,
  type EmbedFieldSpec,
  type EmbedSpec,
  type EventSummary,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmbedPreview } from '../components/EmbedPreview'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { BracketsPage } from './Brackets'
import { EventDetailPanel } from './EventDetailPanel'
import { GiveawaysPage } from './Giveaways'
import { PollsPage } from './Polls'

type StatusFilter = 'open' | 'closed'
type EventsTab = 'events' | 'giveaways' | 'polls' | 'brackets'

function parseEventsTab(raw: string | null): EventsTab {
  if (raw === 'giveaways' || raw === 'polls' || raw === 'brackets') return raw
  return 'events'
}

function TabBar({ tab, setTab, t }: { tab: EventsTab; setTab: (t: EventsTab) => void; t: (key: string) => string }) {
  const tabs: { key: EventsTab; labelKey: string; icon: typeof CalendarCheck }[] = [
    { key: 'events', labelKey: 'events.tab.events', icon: CalendarCheck },
    { key: 'giveaways', labelKey: 'events.tab.giveaways', icon: Gift },
    { key: 'polls', labelKey: 'events.tab.polls', icon: ChartBar },
    { key: 'brackets', labelKey: 'events.tab.brackets', icon: Trophy },
  ]
  return (
    <div className="flex gap-1 border-b border-border">
      {tabs.map(({ key, labelKey, icon: Icon }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          <Icon size={15} />
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

function emptyCreateSpec(): CreateEventSpec {
  return {
    channel_id: '',
    type: 'tournament',
    title: '',
    description: '',
    banner_url: '',
    ping: 'none',
    mode: 'solo',
    require_info: false,
    max_limit: 0,
    team_size: 5,
    role_reward: null,
    options: [],
    multi_select: false,
  }
}

function modeLabel(mode: CreateEventSpec['mode'], t: (key: string) => string): string {
  if (mode === 'solo') return t('events.mode.solo')
  if (mode === 'team_captain') return t('events.mode.teamCaptain')
  return t('events.mode.teamCode')
}

function buildEventEmbedPreview(spec: CreateEventSpec, optionsText: string, t: (key: string) => string): EmbedSpec {
  const fields: EmbedFieldSpec[] =
    spec.type === 'tournament'
      ? [
          { name: t('events.preview.format'), value: modeLabel(spec.mode, t), inline: true },
          spec.max_limit > 0
            ? { name: t('events.preview.limit'), value: `0 / ${spec.max_limit}`, inline: true }
            : { name: t('events.preview.participants'), value: '0', inline: true },
        ]
      : optionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean)
          .map((opt) => ({ name: opt, value: t('events.preview.votes'), inline: false }))

  return {
    title: spec.title,
    description: spec.description,
    url: '',
    color: spec.type === 'tournament' ? '#ed4245' : '#a8283c',
    author: { name: '', url: '', icon_url: '' },
    footer: { text: t('events.preview.statusOpen'), icon_url: '' },
    image: { url: spec.banner_url },
    thumbnail: { url: '' },
    timestamp: null,
    fields,
  }
}

export function EventsPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = parseEventsTab(searchParams.get('tab'))
  const setTab = (next: EventsTab) => {
    if (next === 'events') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }
  const [status, setStatus] = useState<StatusFilter>('open')
  const [events, setEvents] = useState<EventSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [createOpen, setCreateOpen] = useState(false)
  const [createSpec, setCreateSpec] = useState<CreateEventSpec>(emptyCreateSpec())
  const [optionsText, setOptionsText] = useState('')
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)

  const reload = () => {
    fetchEvents(status)
      .then(setEvents)
      .catch(() => setError(t('events.errorLoad')))
    fetchChannels().then(setChannels).catch(() => {})
    fetchRoles().then(setRoles).catch(() => {})
  }

  useEffect(reload, [status])

  const openCreate = () => {
    setCreateSpec(emptyCreateSpec())
    setOptionsText('')
    setCreateError('')
    setCreateOpen(true)
  }

  const saveCreate = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      const spec: CreateEventSpec = {
        ...createSpec,
        options: optionsText
          .split('\n')
          .map((line) => line.trim())
          .filter(Boolean),
      }
      await createEvent(spec)
      setCreateOpen(false)
      reload()
    } catch (err) {
      setCreateError(formatApiError(err, t, 'events.errorCreate'))
    } finally {
      setCreateBusy(false)
    }
  }

  if (tab === 'giveaways') {
    return (
      <div className="flex flex-col gap-4">
        <TabBar tab={tab} setTab={setTab} t={t} />
        <GiveawaysPage />
      </div>
    )
  }

  if (tab === 'polls') {
    return (
      <div className="flex flex-col gap-4">
        <TabBar tab={tab} setTab={setTab} t={t} />
        <PollsPage embedded />
      </div>
    )
  }

  if (tab === 'brackets') {
    return (
      <div className="flex flex-col gap-4">
        <TabBar tab={tab} setTab={setTab} t={t} />
        <BracketsPage embedded />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <TabBar tab={tab} setTab={setTab} t={t} />
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="mb-4 flex items-center gap-3">
          <h1 className="text-lg font-semibold text-foreground">{t('events.title')}</h1>
          <Button variant="primary" onClick={openCreate} className="ml-auto">
            {t('events.create')}
          </Button>
          <label className="text-sm text-muted" htmlFor="event-status">
            {t('common.status')}
          </label>
          <Select
            id="event-status"
            value={status}
            onChange={(id) => setStatus(id as StatusFilter)}
            options={[
              { id: 'open', name: t('events.status.open') },
              { id: 'closed', name: t('events.status.closed') },
            ]}
            className="w-40"
          />
        </div>

        {error && <p className="mb-4 text-sm text-danger">{error}</p>}

        <div className="flex flex-col gap-2">
          {events.map((ev) => (
            <Card key={ev.message_id} interactive className="!p-3" onClick={() => setSelectedId(ev.message_id)}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-foreground">{ev.title}</p>
                  <p className="text-xs text-muted">
                    {ev.type === 'tournament' ? t('events.type.tournament') : t('events.type.poll')} · {ev.count}
                  </p>
                </div>
              </div>
            </Card>
          ))}
          {events.length === 0 && <p className="text-sm text-muted">{t('events.empty')}</p>}
        </div>
      </div>

      {selectedId && (
        <div className="w-96 shrink-0">
          <EventDetailPanel
            messageId={selectedId}
            onClose={() => setSelectedId(null)}
            onChanged={() => {
              setSelectedId(null)
              reload()
            }}
          />
        </div>
      )}

      <Modal open={createOpen} title={t('events.modal.create')} onClose={() => setCreateOpen(false)}>
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <div className="flex gap-2">
            <Button
              variant={createSpec.type === 'tournament' ? 'primary' : 'secondary'}
              onClick={() => setCreateSpec((prev) => ({ ...prev, type: 'tournament' }))}
            >
              {t('events.type.tournament')}
            </Button>
            <Button
              variant={createSpec.type === 'poll' ? 'primary' : 'secondary'}
              onClick={() => setCreateSpec((prev) => ({ ...prev, type: 'poll' }))}
            >
              {t('events.type.poll')}
            </Button>
          </div>

          <div data-testid="event-embed-preview">
            <EmbedPreview content="" embed={buildEventEmbedPreview(createSpec, optionsText, t)} />
          </div>

          <label className="text-sm text-muted" htmlFor="event-title">
            {t('events.field.title')}
          </label>
          <input
            id="event-title"
            value={createSpec.title}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, title: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-description">
            {t('events.field.description')}
          </label>
          <textarea
            id="event-description"
            value={createSpec.description}
            onChange={(e) => {
              setCreateSpec((prev) => ({ ...prev, description: e.target.value }))
              e.target.style.height = 'auto'
              e.target.style.height = `${e.target.scrollHeight}px`
            }}
            rows={8}
            className="min-h-[180px] resize-none overflow-hidden rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-banner">
            {t('events.field.banner')}
          </label>
          <input
            id="event-banner"
            value={createSpec.banner_url}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, banner_url: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="event-ping">
            {t('events.field.ping')}
          </label>
          <Select
            id="event-ping"
            value={createSpec.ping}
            onChange={(id) => setCreateSpec((prev) => ({ ...prev, ping: id as CreateEventSpec['ping'] }))}
            options={[
              { id: 'none', name: t('events.ping.none') },
              { id: 'everyone', name: '@everyone' },
              { id: 'here', name: '@here' },
            ]}
          />

          <label className="text-sm text-muted" htmlFor="event-channel">
            {t('common.channel')}
          </label>
          <Select
            id="event-channel"
            value={createSpec.channel_id}
            onChange={(id) => setCreateSpec((prev) => ({ ...prev, channel_id: id }))}
            options={channels}
            placeholder={t('common.selectChannel')}
          />

          {createSpec.type === 'tournament' ? (
            <>
              <label className="text-sm text-muted" htmlFor="event-mode">
                {t('events.field.mode')}
              </label>
              <Select
                id="event-mode"
                value={createSpec.mode}
                onChange={(id) => setCreateSpec((prev) => ({ ...prev, mode: id as CreateEventSpec['mode'] }))}
                options={[
                  { id: 'solo', name: t('events.mode.solo') },
                  { id: 'team_captain', name: t('events.mode.teamCaptain') },
                  { id: 'team_code', name: t('events.mode.teamCode') },
                ]}
              />

              <Toggle
                checked={createSpec.require_info}
                onChange={(v) => setCreateSpec((prev) => ({ ...prev, require_info: v }))}
                label={t('events.field.requireInfo')}
              />

              <label className="text-sm text-muted" htmlFor="event-max-limit">
                {t('events.field.maxLimit')}
              </label>
              <input
                id="event-max-limit"
                type="number"
                min={0}
                value={createSpec.max_limit}
                onChange={(e) => setCreateSpec((prev) => ({ ...prev, max_limit: Number(e.target.value) }))}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />

              {createSpec.mode !== 'solo' && (
                <>
                  <label className="text-sm text-muted" htmlFor="event-team-size">
                    {t('events.field.teamSize')}
                  </label>
                  <input
                    id="event-team-size"
                    type="number"
                    min={2}
                    value={createSpec.team_size}
                    onChange={(e) => setCreateSpec((prev) => ({ ...prev, team_size: Number(e.target.value) }))}
                    className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                  />
                </>
              )}

              <label className="text-sm text-muted" htmlFor="event-role-reward">
                {t('events.field.roleReward')}
              </label>
              <Select
                id="event-role-reward"
                value={createSpec.role_reward ?? ''}
                onChange={(id) => setCreateSpec((prev) => ({ ...prev, role_reward: id || null }))}
                options={roles}
                placeholder={t('events.noRole')}
              />
            </>
          ) : (
            <>
              <label className="text-sm text-muted" htmlFor="event-options">
                {t('events.field.options')}
              </label>
              <textarea
                id="event-options"
                value={optionsText}
                onChange={(e) => setOptionsText(e.target.value)}
                rows={4}
                className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              />

              <Toggle
                checked={createSpec.multi_select}
                onChange={(v) => setCreateSpec((prev) => ({ ...prev, multi_select: v }))}
                label={t('events.field.multiSelect')}
              />
            </>
          )}

          {createError && <p className="text-sm text-danger">{createError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)} disabled={createBusy}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={saveCreate} disabled={createBusy}>
              {createBusy ? t('common.creating') : t('common.create')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
    </div>
  )
}
