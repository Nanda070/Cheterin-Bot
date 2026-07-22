import {
  Cake,
  Gear,
  Plus,
  Ticket as TicketIcon,
  Trash,
  UsersThree,
} from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import { useEffect, useState } from 'react'
import {
  decideFamilyTicket,
  deleteFamilyBirthday,
  fetchChannels,
  fetchEmojis,
  fetchFamilyBirthdays,
  fetchFamilyRoster,
  fetchFamilySettings,
  fetchFamilyTickets,
  fetchMembers,
  fetchRoles,
  setFamilyBirthday,
  updateFamilySettings,
  type ChannelInfo,
  type CustomEmoji,
  type FamilyBirthday,
  type FamilyRosterGroup,
  type FamilySettings,
  type FamilyTicket,
  type FamilyTicketStatus,
  type FamilyTicketsPage,
  type MemberSummary,
  type RoleInfo,
} from '../api/client'
import { ChipPicker } from '../components/ChipPicker'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

type Tab = 'settings' | 'roster' | 'tickets' | 'birthdays'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function ticketStatusLabel(status: FamilyTicketStatus, t: (k: string) => string) {
  const m: Record<FamilyTicketStatus, string> = {
    open: 'family.tickets.status.open',
    approved: 'family.tickets.status.approved',
    denied: 'family.tickets.status.denied',
    closed: 'family.tickets.status.closed',
  }
  return t(m[status])
}

export function FamilyPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<FamilySettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [emojis, setEmojis] = useState<CustomEmoji[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  const [roster, setRoster] = useState<FamilyRosterGroup[] | null>(null)

  const [ticketStatus, setTicketStatus] = useState<FamilyTicketStatus | ''>('open')
  const [ticketPage, setTicketPage] = useState(1)
  const [tickets, setTickets] = useState<FamilyTicketsPage | null>(null)
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null)

  const [birthdays, setBirthdays] = useState<FamilyBirthday[] | null>(null)
  const [birthdaySearch, setBirthdaySearch] = useState('')
  const [birthdayResults, setBirthdayResults] = useState<MemberSummary[]>([])
  const [birthdayTarget, setBirthdayTarget] = useState<MemberSummary | null>(null)
  const [birthdayDate, setBirthdayDate] = useState('')
  const [birthdayError, setBirthdayError] = useState('')

  useEffect(() => {
    Promise.all([fetchFamilySettings(), fetchChannels(), fetchRoles(), fetchEmojis()])
      .then(([s, ch, rl, em]) => {
        setSettings(s)
        setChannels(ch)
        setRoles(rl)
        setEmojis(em)
      })
      .catch(() => setError(t('family.errorLoad')))
  }, [])

  useEffect(() => {
    if (tab !== 'roster') return
    fetchFamilyRoster()
      .then((r) => setRoster(r.groups))
      .catch(() => setError(t('family.errorLoadRoster')))
  }, [tab])

  useEffect(() => {
    if (tab !== 'tickets') return
    fetchFamilyTickets(ticketStatus, ticketPage)
      .then(setTickets)
      .catch(() => setError(t('family.errorLoadTickets')))
  }, [tab, ticketStatus, ticketPage])

  useEffect(() => {
    if (tab !== 'birthdays') return
    fetchFamilyBirthdays()
      .then((b) => setBirthdays(b.entries))
      .catch(() => setError(t('family.errorLoadBirthdays')))
  }, [tab])

  useEffect(() => {
    if (!birthdaySearch) {
      setBirthdayResults([])
      return
    }
    const timer = setTimeout(() => {
      fetchMembers(birthdaySearch, 1)
        .then((page) => setBirthdayResults(page.members))
        .catch(() => {})
    }, 300)
    return () => clearTimeout(timer)
  }, [birthdaySearch])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const patch = (updater: (prev: FamilySettings) => FamilySettings) => {
    setSettings((prev) => (prev ? updater(prev) : prev))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateFamilySettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch {
      setError(t('family.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const decide = async (ticket: FamilyTicket, decision: 'approve' | 'deny' | 'close') => {
    setBusy(true)
    setError('')
    try {
      await decideFamilyTicket(ticket.user_id, decision)
      setTickets(await fetchFamilyTickets(ticketStatus, ticketPage))
    } catch {
      setError(t('family.errorDecide'))
    } finally {
      setBusy(false)
    }
  }

  const addBirthday = async () => {
    if (!birthdayTarget || !birthdayDate.trim()) return
    setBirthdayError('')
    try {
      await setFamilyBirthday(birthdayTarget.id, birthdayDate.trim())
      setBirthdays((await fetchFamilyBirthdays()).entries)
      setBirthdayTarget(null)
      setBirthdaySearch('')
      setBirthdayDate('')
    } catch {
      setBirthdayError(t('family.errorBirthdaySave'))
    }
  }

  const removeBirthday = async (userId: string) => {
    setBusy(true)
    setError('')
    try {
      await deleteFamilyBirthday(userId)
      setBirthdays((await fetchFamilyBirthdays()).entries)
    } catch {
      setError(t('family.errorBirthdayDelete'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-4xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <UsersThree size={22} className="text-primary" />
          {t('family.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('common.moduleEnabled') : t('common.moduleDisabled')}
        />
      </div>
      <p className="text-sm text-muted">
{t('family.intro')}
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-1 border-b border-border">
        {[
          { key: 'settings' as Tab, labelKey: 'common.settings', icon: Gear },
          { key: 'roster' as Tab, labelKey: 'family.tab.roster', icon: UsersThree },
          { key: 'tickets' as Tab, labelKey: 'family.tab.tickets', icon: TicketIcon },
          { key: 'birthdays' as Tab, labelKey: 'family.tab.birthdays', icon: Cake },
        ].map(({ key, labelKey, icon: Icon }) => (
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

      {tab === 'settings' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('family.roster.title')}</h2>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="family-list-channel">
                {t('family.roster.listChannel')}
              </label>
              <Select
                id="family-list-channel"
                value={settings.roster.list_channel_id}
                onChange={(id) => patch((p) => ({ ...p, roster: { ...p.roster, list_channel_id: id } }))}
                options={channels}
                placeholder={t('family.roster.anyChannel')}
              />
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted">{t('family.roster.roles')}</p>
              {settings.roster.target_roles.map((entry, index) => (
                <div key={index} className="flex flex-wrap items-center gap-2">
                  <input
                    value={entry.label}
                    onChange={(e) =>
                      patch((p) => ({
                        ...p,
                        roster: {
                          ...p.roster,
                          target_roles: p.roster.target_roles.map((r, i) =>
                            i === index ? { ...r, label: e.target.value } : r,
                          ),
                        },
                      }))
                    }
                    placeholder={t('family.roster.groupPlaceholder')}
                    className={`${inputClass} min-w-40 flex-1`}
                  />
                  <Select
                    value={entry.role_id}
                    onChange={(id) =>
                      patch((p) => ({
                        ...p,
                        roster: {
                          ...p.roster,
                          target_roles: p.roster.target_roles.map((r, i) =>
                            i === index ? { ...r, role_id: id } : r,
                          ),
                        },
                      }))
                    }
                    options={roles}
                    placeholder={t('family.roster.rolePlaceholder')}
                    className="min-w-40 flex-1"
                  />
                  <Button
                    variant="ghost"
                    onClick={() =>
                      patch((p) => ({
                        ...p,
                        roster: {
                          ...p.roster,
                          target_roles: p.roster.target_roles.filter((_, i) => i !== index),
                        },
                      }))
                    }
                  >
                    <Trash size={16} />
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                onClick={() =>
                  patch((p) => ({
                    ...p,
                    roster: { ...p.roster, target_roles: [...p.roster.target_roles, { label: '', role_id: '' }] },
                  }))
                }
              >
                <Plus size={16} />
                {t('family.roster.addRole')}
              </Button>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('family.applications.title')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-app-channel">
                  {t('family.applications.channel')}
                </label>
                <Select
                  id="family-app-channel"
                  value={settings.applications.application_channel_id}
                  onChange={(id) =>
                    patch((p) => ({ ...p, applications: { ...p.applications, application_channel_id: id } }))
                  }
                  options={channels}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-log-channel">
                  {t('family.applications.logChannel')}
                </label>
                <Select
                  id="family-log-channel"
                  value={settings.applications.log_channel_id}
                  onChange={(id) => patch((p) => ({ ...p, applications: { ...p.applications, log_channel_id: id } }))}
                  options={channels}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-ticket-manager-role">
                  {t('family.applications.ticketManagerRole')}
                </label>
                <Select
                  id="family-ticket-manager-role"
                  value={settings.applications.ticket_manager_role_id}
                  onChange={(id) =>
                    patch((p) => ({ ...p, applications: { ...p.applications, ticket_manager_role_id: id } }))
                  }
                  options={roles}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-notify-role">
                  {t('family.applications.notifyRole')}
                </label>
                <Select
                  id="family-notify-role"
                  value={settings.applications.notify_role_id}
                  onChange={(id) => patch((p) => ({ ...p, applications: { ...p.applications, notify_role_id: id } }))}
                  options={roles}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-active-role">
                  {t('family.applications.activeRole')}
                </label>
                <Select
                  id="family-active-role"
                  value={settings.applications.ticket_active_role_id}
                  onChange={(id) =>
                    patch((p) => ({ ...p, applications: { ...p.applications, ticket_active_role_id: id } }))
                  }
                  options={roles}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-archive-minutes">
                  {t('family.applications.archiveMinutes')}
                </label>
                <Select
                  id="family-archive-minutes"
                  value={String(settings.applications.thread_archive_minutes)}
                  onChange={(id) =>
                    patch((p) => ({ ...p, applications: { ...p.applications, thread_archive_minutes: Number(id) } }))
                  }
                  options={[
                    { id: '60', name: t('family.applications.archive.1h') },
                    { id: '1440', name: t('family.applications.archive.1d') },
                    { id: '4320', name: t('family.applications.archive.3d') },
                    { id: '10080', name: t('family.applications.archive.7d') },
                  ]}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-yes-emoji">
                  {t('family.applications.yesEmoji')}
                </label>
                <Select
                  id="family-yes-emoji"
                  value={settings.applications.yes_emoji_id}
                  onChange={(id) => patch((p) => ({ ...p, applications: { ...p.applications, yes_emoji_id: id } }))}
                  options={emojis}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-no-emoji">
                  {t('family.applications.noEmoji')}
                </label>
                <Select
                  id="family-no-emoji"
                  value={settings.applications.no_emoji_id}
                  onChange={(id) => patch((p) => ({ ...p, applications: { ...p.applications, no_emoji_id: id } }))}
                  options={emojis}
                  placeholder={t('common.notSet')}
                />
              </div>
            </div>
            <ChipPicker
              label={t('family.applications.staffRoles')}
              options={roles}
              selected={settings.applications.staff_role_ids}
              onChange={(ids) => patch((p) => ({ ...p, applications: { ...p.applications, staff_role_ids: ids } }))}
            />
            <ChipPicker
              label={t('family.applications.approveRoles')}
              options={roles}
              selected={settings.applications.approve_role_ids}
              onChange={(ids) => patch((p) => ({ ...p, applications: { ...p.applications, approve_role_ids: ids } }))}
            />
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('family.birthdays.title')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-bday-channel">
                  {t('family.birthdays.channel')}
                </label>
                <Select
                  id="family-bday-channel"
                  value={settings.birthdays.channel_id}
                  onChange={(id) => patch((p) => ({ ...p, birthdays: { ...p.birthdays, channel_id: id } }))}
                  options={channels}
                  placeholder={t('common.notSet')}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="family-bday-list-channel">
                  {t('family.birthdays.listChannel')}
                </label>
                <Select
                  id="family-bday-list-channel"
                  value={settings.birthdays.list_channel_id}
                  onChange={(id) => patch((p) => ({ ...p, birthdays: { ...p.birthdays, list_channel_id: id } }))}
                  options={channels}
                  placeholder={t('common.notSet')}
                />
              </div>
            </div>
          </Card>

          {saved && <p className="text-sm text-primary">{saved}</p>}
          <div>
            <Button variant="primary" onClick={save} disabled={busy}>
              {busy ? t('common.saving') : t('common.save')}
            </Button>
          </div>
        </div>
      )}

      {tab === 'roster' && (
        <div className="flex flex-col gap-3">
          {!roster && <p className="text-sm text-muted">{t('common.loading')}</p>}
          {roster && roster.length === 0 && (
            <p className="text-sm text-muted">{t('family.roster.notConfigured')}</p>
          )}
          {roster?.map((group) => (
            <Card key={group.role_id || group.label} className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-foreground">{group.label}</h2>
                <span className="text-xs text-muted">{t('family.roster.memberCount', { count: group.members.length })}</span>
              </div>
              {!group.role_found && <p className="text-xs text-danger">{t('family.roster.roleNotFound')}</p>}
              {group.members.length === 0 ? (
                <p className="text-sm text-muted">{t('family.roster.absent')}</p>
              ) : (
                <ul className="flex flex-col gap-0.5">
                  {group.members.map((m) => (
                    <li key={m.id} className="text-sm text-foreground">
                      {m.display}
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          ))}
        </div>
      )}

      {tab === 'tickets' && (
        <div className="flex flex-col gap-3">
          <Select
            value={ticketStatus}
            onChange={(id) => {
              setTicketStatus(id as FamilyTicketStatus | '')
              setTicketPage(1)
            }}
            options={[
              { id: '', name: t('family.tickets.allStatuses') },
              { id: 'open', name: t('family.tickets.status.open') },
              { id: 'approved', name: t('family.tickets.status.approved') },
              { id: 'denied', name: t('family.tickets.status.denied') },
              { id: 'closed', name: t('family.tickets.status.closed') },
            ]}
            className="w-56"
          />

          {!tickets && <p className="text-sm text-muted">{t('common.loading')}</p>}
          {tickets && tickets.entries.length === 0 && <p className="text-sm text-muted">{t('family.tickets.empty')}</p>}
          {tickets?.entries.map((ticket) => (
            <Card key={ticket.user_id} className="flex flex-col gap-2">
              <button
                type="button"
                className="flex cursor-pointer items-center justify-between text-left"
                onClick={() => setExpandedTicket((prev) => (prev === ticket.user_id ? null : ticket.user_id))}
              >
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {ticket.nickname} · {ticket.display}
                  </p>
                  <p className="text-xs text-muted">
                    {ticketStatusLabel(ticket.status, t)} · {ticket.created_at}
                  </p>
                </div>
                {ticket.status === 'open' && (
                  <div className="flex shrink-0 gap-1.5" onClick={(e) => e.stopPropagation()}>
                    <Button variant="secondary" onClick={() => decide(ticket, 'approve')} disabled={busy}>
                      {t('common.approve')}
                    </Button>
                    <Button variant="danger" onClick={() => decide(ticket, 'deny')} disabled={busy}>
                      {t('family.tickets.reject')}
                    </Button>
                    <Button variant="ghost" onClick={() => decide(ticket, 'close')} disabled={busy}>
                      {t('common.close')}
                    </Button>
                  </div>
                )}
              </button>
              {expandedTicket === ticket.user_id && (
                <div className="grid gap-x-4 gap-y-1 border-t border-border pt-2 text-sm sm:grid-cols-2">
                  <p><span className="text-muted">{t('family.tickets.gameLevel')}</span> {ticket.game_level}</p>
                  <p><span className="text-muted">{t('family.tickets.factions')}</span> {ticket.faction_pref}</p>
                  <p className="sm:col-span-2"><span className="text-muted">{t('family.tickets.onlineTimezone')}</span> {ticket.online_timezone}</p>
                  <p><span className="text-muted">{t('family.tickets.name')}</span> {ticket.real_name}</p>
                  <p><span className="text-muted">{t('family.tickets.age')}</span> {ticket.real_age}</p>
                  <p className="sm:col-span-2"><span className="text-muted">{t('family.tickets.about')}</span> {ticket.about_text}</p>
                  <p className="sm:col-span-2"><span className="text-muted">{t('family.tickets.whyJoin')}</span> {ticket.why_join}</p>
                  <p className="sm:col-span-2"><span className="text-muted">{t('family.tickets.inviter')}</span> {ticket.inviter_nickname || '—'}</p>
                </div>
              )}
            </Card>
          ))}

          {tickets && tickets.total > tickets.page_size && (
            <div className="flex items-center justify-center gap-3">
              <Button variant="ghost" disabled={ticketPage <= 1} onClick={() => setTicketPage((p) => p - 1)}>
                {t('family.tickets.prev')}
              </Button>
              <span className="text-sm text-muted">
                {t('family.tickets.page', { page: tickets.page, total: Math.ceil(tickets.total / tickets.page_size) })}
              </span>
              <Button
                variant="ghost"
                disabled={ticketPage >= Math.ceil(tickets.total / tickets.page_size)}
                onClick={() => setTicketPage((p) => p + 1)}
              >
                {t('family.tickets.next')}
              </Button>
            </div>
          )}
        </div>
      )}

      {tab === 'birthdays' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('family.birthdays.addDate')}</h2>
            <div className="flex flex-wrap gap-2">
              <div className="relative min-w-48 flex-1">
                <input
                  value={birthdayTarget ? birthdayTarget.display_name : birthdaySearch}
                  onChange={(e) => {
                    setBirthdayTarget(null)
                    setBirthdaySearch(e.target.value)
                  }}
                  placeholder={t('family.birthdays.searchPlaceholder')}
                  className={inputClass + ' w-full'}
                />
                {!birthdayTarget && birthdayResults.length > 0 && (
                  <div className="absolute left-0 top-full z-10 mt-1 max-h-48 w-full overflow-y-auto rounded-card border border-border bg-surface p-1.5 shadow-[0_12px_28px_-8px_rgba(0,0,0,0.6)]">
                    {birthdayResults.map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => {
                          setBirthdayTarget(m)
                          setBirthdayResults([])
                        }}
                        className="flex w-full cursor-pointer items-center rounded-[8px] px-3 py-2 text-left text-sm text-foreground hover:bg-surface-hover"
                      >
                        {m.display_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <input
                value={birthdayDate}
                onChange={(e) => setBirthdayDate(e.target.value)}
                placeholder={t('family.birthdays.datePlaceholder')}
                className={inputClass + ' w-44'}
              />
              <Button variant="primary" onClick={addBirthday} disabled={!birthdayTarget || !birthdayDate.trim()}>
                {t('common.save')}
              </Button>
            </div>
            {birthdayError && <p className="text-sm text-danger">{birthdayError}</p>}
          </Card>

          <Card className="p-0">
            {!birthdays && <p className="p-4 text-sm text-muted">{t('common.loading')}</p>}
            {birthdays && birthdays.length === 0 && <p className="p-4 text-sm text-muted">{t('family.birthdays.empty')}</p>}
            {birthdays?.map((b) => (
              <div
                key={b.user_id}
                className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5 last:border-b-0"
              >
                <div>
                  <p className="text-sm text-foreground">{b.display}</p>
                  <p className="text-xs text-muted">{b.date_display}</p>
                </div>
                <Button variant="ghost" onClick={() => removeBirthday(b.user_id)} disabled={busy}>
                  <Trash size={16} />
                </Button>
              </div>
            ))}
          </Card>
        </div>
      )}
    </div>
  )
}
