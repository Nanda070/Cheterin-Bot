import { Crosshair } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  cancelCustomsLobby,
  createCustomsLobby,
  createCustomsSchedule,
  deleteCustomsSchedule,
  fetchCategories,
  fetchChannels,
  fetchCustomsLobbies,
  fetchCustomsSettings,
  fetchRoles,
  kickCustomsPlayer,
  rematchCustomsLobby,
  setCustomsLobbyBans,
  setCustomsLobbyTeams,
  setCustomsLobbyScore,
  updateCustomsSettings,
  type ChannelInfo,
  customsPlayerLabel,
  type CustomsLobbySummary,
  type CustomsPingMode,
  type CustomsSchedule,
  type CustomsSettings,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

type CreateSpec = {
  name: string
  notes: string
  join_mode: 'solo' | 'team_code'
  channel_id: string
  ping: CustomsPingMode
  signup_minutes: number
}

function emptyCreate(settings: CustomsSettings | null): CreateSpec {
  return {
    name: settings?.default_name || '',
    notes: settings?.default_notes || '',
    join_mode: settings?.default_mode === 'team_code' ? 'team_code' : 'solo',
    channel_id: settings?.channel_id || '',
    ping: settings?.default_ping || 'none',
    signup_minutes: settings?.default_signup_minutes || 0,
  }
}

function pingOptions(t: (key: string) => string) {
  return [
    { id: 'none', name: t('customs.ping.none') },
    { id: 'participants', name: t('customs.ping.participants') },
    { id: 'role', name: t('customs.ping.role') },
  ]
}

function weekdayOptions(t: (key: string) => string) {
  return [0, 1, 2, 3, 4, 5, 6].map((d) => ({ id: String(d), name: t(`customs.weekday.${d}`) }))
}

function emptySchedule(settings: CustomsSettings): Omit<CustomsSchedule, 'id' | 'last_run'> {
  return {
    enabled: true,
    weekday: 4,
    hour: 21,
    minute: 0,
    name: settings.default_name || 'Кастомка',
    notes: settings.default_notes || '',
    join_mode: settings.default_mode === 'team_code' ? 'team_code' : 'solo',
    channel_id: settings.channel_id || '',
    ping: settings.default_ping || 'none',
    signup_minutes: settings.default_signup_minutes || 0,
  }
}

function LobbyCard({
  lob,
  maps,
  selected,
  onSelect,
  onCancel,
  onRematch,
  onKick,
  onBans,
  onTeams,
  onScore,
  t,
}: {
  lob: CustomsLobbySummary
  maps: CustomsSettings['maps']
  selected: boolean
  onSelect: () => void
  onCancel?: () => void
  onRematch: () => void
  onKick?: (userId: string) => void
  onBans?: (ids: string[]) => void
  onTeams?: (teamA: string[], teamB: string[]) => void
  onScore?: (a: number, b: number) => void
  t: (key: string) => string
}) {
  const [scoreA, setScoreA] = useState(String(lob.score?.a ?? 13))
  const [scoreB, setScoreB] = useState(String(lob.score?.b ?? 0))
  const active = ['open', 'checkin', 'ready', 'live'].includes(lob.status)
  const enabledMaps = maps.filter((m) => m.enabled !== false)
  const [teamA, setTeamA] = useState<string[]>(lob.team_a?.map((p) => p.user_id) || [])

  const toggleBan = (mapId: string) => {
    if (!onBans) return
    const current = lob.banned_maps || []
    if (current.includes(mapId)) {
      onBans(current.filter((id) => id !== mapId))
      return
    }
    if (current.length >= 2) return
    onBans([...current, mapId])
  }

  return (
    <div className="rounded-control border border-border px-3 py-2">
      <button type="button" className="flex w-full items-start justify-between gap-2 text-left" onClick={onSelect}>
        <div>
          <p className="text-sm text-foreground">{lob.name}</p>
          <p className="text-xs text-muted">
            {lob.join_mode === 'team_code' ? t('customs.mode.teamCode') : t('customs.mode.solo')} · {lob.players}/
            {lob.max_players} · {t(`customs.status.${lob.status}`)}
            {lob.map_name ? ` · ${lob.map_name}` : ''}
          </p>
        </div>
      </button>
      {selected && (
        <div className="mt-3 flex flex-col gap-3 border-t border-border pt-3">
          {active && (
            <div>
              <p className="mb-1 text-sm text-foreground">{t('customs.playersTitle')}</p>
              {(lob.players_list || []).length === 0 ? (
                <p className="text-xs text-muted">{t('customs.noPlayers')}</p>
              ) : (
                <ul className="flex flex-col gap-1">
                  {(lob.players_list || []).map((p) => (
                    <li key={p.user_id} className="flex items-center justify-between gap-2 text-sm">
                      <span className="text-muted">
                        {customsPlayerLabel(p)} · {p.rank_name || p.rank}
                        {p.team_code ? ` · ${p.team_code}` : ''}
                      </span>
                      {onKick && (
                        <Button variant="ghost" onClick={() => onKick(p.user_id)}>
                          {t('customs.kick')}
                        </Button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {active && onTeams && (lob.players_list || []).length > 0 && (
            <div className="flex flex-col gap-2">
              <div>
                <p className="text-sm text-foreground">{t('customs.manualTeamsTitle')}</p>
                <p className="text-xs text-muted">{t('customs.manualTeamsHint')}</p>
              </div>
              <div className="grid gap-1 sm:grid-cols-2">
                {(lob.players_list || []).map((p) => {
                  const inA = teamA.includes(p.user_id)
                  return (
                    <div key={`team-${p.user_id}`} className="flex items-center justify-between gap-2 rounded border border-border px-2 py-1">
                      <span className="truncate text-xs text-muted">{customsPlayerLabel(p)}</span>
                      <Button
                        variant={inA ? 'primary' : 'ghost'}
                        onClick={() => setTeamA((current) => (inA ? current.filter((id) => id !== p.user_id) : [...current, p.user_id]))}
                      >
                        A
                      </Button>
                    </div>
                  )
                })}
              </div>
              <Button
                variant="secondary"
                disabled={teamA.length > 5 || (lob.players_list || []).length - teamA.length > 5}
                onClick={() => onTeams(teamA, (lob.players_list || []).map((p) => p.user_id).filter((id) => !teamA.includes(id)))}
              >
                {t('customs.manualTeamsSave')}
              </Button>
            </div>
          )}
          {active && onBans && (
            <div>
              <p className="mb-1 text-sm text-foreground">{t('customs.bansTitle')}</p>
              <p className="mb-2 text-xs text-muted">{t('customs.bansHint')}</p>
              <div className="grid gap-1 sm:grid-cols-2">
                {enabledMaps.map((map) => (
                  <Toggle
                    key={map.id}
                    checked={(lob.banned_maps || []).includes(map.id)}
                    onChange={() => toggleBan(map.id)}
                    label={map.name}
                  />
                ))}
              </div>
            </div>
          )}
          {lob.status === 'live' && onScore && (
            <div className="flex flex-wrap items-end gap-2">
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">{t('customs.scoreA')}</span>
                <input
                  type="number"
                  min={0}
                  max={99}
                  value={scoreA}
                  onChange={(e) => setScoreA(e.target.value)}
                  className="w-20 rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                />
              </label>
              <label className="flex flex-col gap-1 text-sm">
                <span className="text-muted">{t('customs.scoreB')}</span>
                <input
                  type="number"
                  min={0}
                  max={99}
                  value={scoreB}
                  onChange={(e) => setScoreB(e.target.value)}
                  className="w-20 rounded-control border border-border bg-background px-2 py-1.5 text-sm text-foreground"
                />
              </label>
              <Button variant="secondary" onClick={() => onScore(Number(scoreA) || 0, Number(scoreB) || 0)}>
                {t('customs.scoreSubmit')}
              </Button>
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={onRematch}>
              {t('customs.rematch')}
            </Button>
            {onCancel && (
              <Button variant="ghost" onClick={onCancel}>
                {t('customs.cancelLobby')}
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function CustomsPage() {
  const t = useT()
  const [settings, setSettings] = useState<CustomsSettings | null>(null)
  const [lobbies, setLobbies] = useState<CustomsLobbySummary[]>([])
  const [recent, setRecent] = useState<CustomsLobbySummary[]>([])
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [categories, setCategories] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [createSpec, setCreateSpec] = useState<CreateSpec>(emptyCreate(null))
  const [createError, setCreateError] = useState('')
  const [createBusy, setCreateBusy] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [schedDraft, setSchedDraft] = useState<Omit<CustomsSchedule, 'id' | 'last_run'> | null>(null)

  const reload = () => {
    fetchCustomsSettings()
      .then(setSettings)
      .catch(() => setError(t('customs.errorLoad')))
    fetchCustomsLobbies('active')
      .then(setLobbies)
      .catch(() => setLobbies([]))
    fetchCustomsLobbies('finished')
      .then((rows) => setRecent(rows.slice(0, 8)))
      .catch(() => setRecent([]))
    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
    fetchCategories()
      .then(setCategories)
      .catch(() => setCategories([]))
    fetchRoles()
      .then(setRoles)
      .catch(() => setRoles([]))
  }

  useEffect(reload, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateCustomsSettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const openCreate = () => {
    setCreateSpec(emptyCreate(settings))
    setCreateError('')
    setCreateOpen(true)
  }

  const publish = async () => {
    setCreateBusy(true)
    setCreateError('')
    try {
      await createCustomsLobby(createSpec)
      setCreateOpen(false)
      reload()
    } catch (err) {
      setCreateError(formatApiError(err, t, 'customs.errorCreate'))
    } finally {
      setCreateBusy(false)
    }
  }

  const cancelLobby = async (id: string) => {
    try {
      await cancelCustomsLobby(id)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorCancel'))
    }
  }

  const rematch = async (id: string) => {
    try {
      await rematchCustomsLobby(id)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorRematch'))
    }
  }

  const kick = async (lobbyId: string, userId: string) => {
    try {
      await kickCustomsPlayer(lobbyId, userId)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorKick'))
    }
  }

  const saveBans = async (lobbyId: string, ids: string[]) => {
    try {
      await setCustomsLobbyBans(lobbyId, ids)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorBans'))
    }
  }

  const saveTeams = async (lobbyId: string, teamA: string[], teamB: string[]) => {
    try {
      await setCustomsLobbyTeams(lobbyId, teamA, teamB)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorTeams'))
    }
  }

  const saveScore = async (lobbyId: string, a: number, b: number) => {
    try {
      await setCustomsLobbyScore(lobbyId, a, b)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorScore'))
    }
  }

  const addSchedule = async () => {
    const draft = schedDraft || emptySchedule(settings)
    try {
      await createCustomsSchedule(draft)
      setSchedDraft(null)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorSchedule'))
    }
  }

  const removeSchedule = async (id: string) => {
    try {
      await deleteCustomsSchedule(id)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'customs.errorSchedule'))
    }
  }

  const toggleDefaultBan = (mapId: string) => {
    const current = settings.default_banned_maps || []
    const next = current.includes(mapId) ? current.filter((id) => id !== mapId) : [...current, mapId]
    setSettings({ ...settings, default_banned_maps: next })
  }

  const roleOptions = [{ id: '', name: t('customs.rank.none') }, ...roles]
  const categoryOptions = [{ id: '', name: t('customs.voiceCategory.none') }, ...categories]
  const resultsOptions = [{ id: '', name: t('customs.resultsChannel.none') }, ...channels]
  const schedules = settings.schedules || []
  const draft = schedDraft || emptySchedule(settings)

  return (
    <div className="flex max-w-5xl flex-col gap-5 pb-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Crosshair size={22} className="text-primary" />
          {t('customs.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('customs.moduleOn') : t('customs.moduleOff')}
        />
        <Button variant="primary" onClick={openCreate} className="ml-auto" disabled={!settings.enabled}>
          {t('customs.create')}
        </Button>
      </div>
      <p className="text-sm text-muted">{t('customs.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-success">{saved}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.lobbiesTitle')}</h2>
        {lobbies.length === 0 ? (
          <p className="text-sm text-muted">{t('customs.lobbiesEmpty')}</p>
        ) : (
          <div className="flex flex-col gap-2">
            {lobbies.map((lob) => (
              <LobbyCard
                key={lob.id}
                lob={lob}
                maps={settings.maps}
                selected={selectedId === lob.id}
                onSelect={() => setSelectedId(selectedId === lob.id ? null : lob.id)}
                onCancel={() => cancelLobby(lob.id)}
                onRematch={() => rematch(lob.id)}
                onKick={(uid) => kick(lob.id, uid)}
                onBans={(ids) => saveBans(lob.id, ids)}
                onTeams={(a, b) => saveTeams(lob.id, a, b)}
                onScore={(a, b) => saveScore(lob.id, a, b)}
                t={t}
              />
            ))}
          </div>
        )}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.recentTitle')}</h2>
        {recent.length === 0 ? (
          <p className="text-sm text-muted">{t('customs.recentEmpty')}</p>
        ) : (
          <div className="flex flex-col gap-2">
            {recent.map((lob) => (
              <LobbyCard
                key={lob.id}
                lob={lob}
                maps={settings.maps}
                selected={selectedId === `r-${lob.id}`}
                onSelect={() => setSelectedId(selectedId === `r-${lob.id}` ? null : `r-${lob.id}`)}
                onRematch={() => rematch(lob.id)}
                t={t}
              />
            ))}
          </div>
        )}
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.defaultsTitle')}</h2>
        <label className="text-sm text-muted" htmlFor="customs-default-name">
          {t('customs.defaultName')}
        </label>
        <input
          id="customs-default-name"
          value={settings.default_name || ''}
          onChange={(e) => setSettings({ ...settings, default_name: e.target.value })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />
        <label className="text-sm text-muted" htmlFor="customs-default-notes">
          {t('customs.defaultNotes')}
        </label>
        <textarea
          id="customs-default-notes"
          value={settings.default_notes || ''}
          onChange={(e) => setSettings({ ...settings, default_notes: e.target.value })}
          rows={2}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />
        <label className="text-sm text-muted" htmlFor="customs-default-mode">
          {t('customs.defaultMode')}
        </label>
        <Select
          id="customs-default-mode"
          value={settings.default_mode}
          onChange={(id) => setSettings({ ...settings, default_mode: id as CustomsSettings['default_mode'] })}
          options={[
            { id: 'solo', name: t('customs.mode.solo') },
            { id: 'team_code', name: t('customs.mode.teamCode') },
          ]}
        />
        <label className="text-sm text-muted" htmlFor="customs-default-ping">
          {t('customs.defaultPing')}
        </label>
        <Select
          id="customs-default-ping"
          value={settings.default_ping || 'none'}
          onChange={(id) => setSettings({ ...settings, default_ping: id as CustomsPingMode })}
          options={pingOptions(t)}
        />
        {(settings.default_ping || 'none') === 'role' && (
          <>
            <label className="text-sm text-muted" htmlFor="customs-ping-role">
              {t('customs.pingRole')}
            </label>
            <Select
              id="customs-ping-role"
              value={settings.ping_role_id || ''}
              onChange={(id) => setSettings({ ...settings, ping_role_id: id })}
              options={roleOptions}
              placeholder={t('common.selectRole')}
            />
          </>
        )}
        <label className="text-sm text-muted" htmlFor="customs-default-signup">
          {t('customs.defaultSignup')}
        </label>
        <input
          id="customs-default-signup"
          type="number"
          min={0}
          max={240}
          value={settings.default_signup_minutes || 0}
          onChange={(e) => setSettings({ ...settings, default_signup_minutes: Number(e.target.value) || 0 })}
          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
        />
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.channelsTitle')}</h2>
        <p className="text-sm text-muted">{t('customs.channelHint')}</p>
        <Select
          id="customs-channel"
          value={settings.channel_id}
          onChange={(id) => setSettings({ ...settings, channel_id: id })}
          options={channels}
          placeholder={t('common.selectChannel')}
        />
        <p className="text-sm text-muted">{t('customs.hostRoleHint')}</p>
        <Select
          id="customs-host-role"
          value={settings.host_role_id}
          onChange={(id) => setSettings({ ...settings, host_role_id: id })}
          options={roleOptions}
          placeholder={t('common.selectRole')}
        />
        <p className="text-sm text-muted">{t('customs.voiceCategoryHint')}</p>
        <Select
          id="customs-voice-category"
          value={settings.voice_category_id || ''}
          onChange={(id) => setSettings({ ...settings, voice_category_id: id })}
          options={categoryOptions}
          placeholder={t('customs.voiceCategory.none')}
        />
        <p className="text-sm text-muted">{t('customs.resultsChannelHint')}</p>
        <Select
          id="customs-results-channel"
          value={settings.results_channel_id || ''}
          onChange={(id) => setSettings({ ...settings, results_channel_id: id })}
          options={resultsOptions}
          placeholder={t('customs.resultsChannel.none')}
        />
        <Toggle
          checked={settings.auto_lobby_vc !== false}
          onChange={(v) => setSettings({ ...settings, auto_lobby_vc: v })}
          label={t('customs.autoLobbyVc')}
        />
        <Toggle
          checked={settings.auto_move_on_start !== false}
          onChange={(v) => setSettings({ ...settings, auto_move_on_start: v })}
          label={t('customs.autoMoveOnStart')}
        />
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.ranksTitle')}</h2>
        <p className="text-sm text-muted">{t('customs.ranksHint')}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {settings.ranks.map((rank) => (
            <label key={rank.id} className="flex flex-col gap-1 text-sm">
              <span className="text-foreground">{rank.name}</span>
              <Select
                id={`customs-rank-${rank.id}`}
                value={settings.rank_roles[rank.id] || ''}
                onChange={(id) =>
                  setSettings({
                    ...settings,
                    rank_roles: { ...settings.rank_roles, [rank.id]: id },
                  })
                }
                options={roleOptions}
                placeholder={t('common.selectRole')}
              />
            </label>
          ))}
        </div>
        <Toggle
          checked={settings.require_rank_role}
          onChange={(v) => setSettings({ ...settings, require_rank_role: v })}
          label={t('customs.requireRank')}
        />
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.mapsTitle')}</h2>
        <p className="text-sm text-muted">{t('customs.mapsHint')}</p>
        <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
          {settings.maps.map((map) => (
            <Toggle
              key={map.id}
              checked={settings.map_pool[map.id] !== false}
              onChange={(v) =>
                setSettings({
                  ...settings,
                  map_pool: { ...settings.map_pool, [map.id]: v },
                })
              }
              label={map.name}
            />
          ))}
        </div>
        <p className="text-sm text-muted">{t('customs.defaultBans')}</p>
        <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
          {settings.maps
            .filter((map) => settings.map_pool[map.id] !== false)
            .map((map) => (
              <Toggle
                key={`ban-${map.id}`}
                checked={(settings.default_banned_maps || []).includes(map.id)}
                onChange={() => toggleDefaultBan(map.id)}
                label={map.name}
              />
            ))}
        </div>
        <Toggle
          checked={settings.avoid_last_map !== false}
          onChange={(v) => setSettings({ ...settings, avoid_last_map: v })}
          label={t('customs.avoidLastMap')}
        />
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.featuresTitle')}</h2>
        <Toggle
          checked={settings.features.voting}
          onChange={(v) => setSettings({ ...settings, features: { ...settings.features, voting: v } })}
          label={t('customs.feature.voting')}
        />
        <Toggle
          checked={settings.features.side_random}
          onChange={(v) => setSettings({ ...settings, features: { ...settings.features, side_random: v } })}
          label={t('customs.feature.side')}
        />
        {settings.features.voting && (
          <label className="flex flex-col gap-1 text-sm">
            <span>{t('customs.voteSeconds')}</span>
            <input
              type="number"
              min={15}
              max={300}
              className="rounded border border-border bg-background px-3 py-2"
              value={settings.vote_seconds}
              onChange={(e) => setSettings({ ...settings, vote_seconds: Number(e.target.value) || 45 })}
            />
          </label>
        )}
        <label className="flex flex-col gap-1 text-sm">
          <span>{t('customs.xpOnWin')}</span>
          <input
            type="number"
            min={0}
            max={50000}
            className="rounded border border-border bg-background px-3 py-2"
            value={settings.xp_on_win}
            onChange={(e) => setSettings({ ...settings, xp_on_win: Number(e.target.value) || 0 })}
          />
        </label>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('customs.scheduleTitle')}</h2>
        <p className="text-sm text-muted">{t('customs.scheduleHint')}</p>
        {schedules.length === 0 ? (
          <p className="text-sm text-muted">{t('customs.scheduleEmpty')}</p>
        ) : (
          <div className="flex flex-col gap-2">
            {schedules.map((sch) => (
              <div key={sch.id} className="flex flex-wrap items-center justify-between gap-2 rounded-control border border-border px-3 py-2">
                <p className="text-sm text-foreground">
                  {sch.name} · {t(`customs.weekday.${sch.weekday}`)} {String(sch.hour).padStart(2, '0')}:
                  {String(sch.minute).padStart(2, '0')}
                </p>
                <Button variant="ghost" onClick={() => removeSchedule(sch.id)}>
                  {t('common.delete')}
                </Button>
              </div>
            ))}
          </div>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted">{t('customs.scheduleName')}</span>
            <input
              value={draft.name}
              onChange={(e) => setSchedDraft({ ...draft, name: e.target.value })}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
            />
          </label>
          <Select
            id="customs-sched-day"
            value={String(draft.weekday)}
            onChange={(id) => setSchedDraft({ ...draft, weekday: Number(id) })}
            options={weekdayOptions(t)}
          />
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted">{t('customs.scheduleTime')}</span>
            <input
              type="time"
              value={`${String(draft.hour).padStart(2, '0')}:${String(draft.minute).padStart(2, '0')}`}
              onChange={(e) => {
                const [h, m] = e.target.value.split(':').map(Number)
                setSchedDraft({ ...draft, hour: h || 0, minute: m || 0 })
              }}
              className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
            />
          </label>
          <Select
            id="customs-sched-mode"
            value={draft.join_mode}
            onChange={(id) => setSchedDraft({ ...draft, join_mode: id as 'solo' | 'team_code' })}
            options={[
              { id: 'solo', name: t('customs.mode.solo') },
              { id: 'team_code', name: t('customs.mode.teamCode') },
            ]}
          />
          <Select
            id="customs-sched-channel"
            value={draft.channel_id}
            onChange={(id) => setSchedDraft({ ...draft, channel_id: id })}
            options={channels}
            placeholder={t('common.selectChannel')}
          />
          <Select
            id="customs-sched-ping"
            value={draft.ping}
            onChange={(id) => setSchedDraft({ ...draft, ping: id as CustomsPingMode })}
            options={pingOptions(t)}
          />
        </div>
        <Button variant="secondary" onClick={addSchedule} className="self-start">
          {t('customs.scheduleAdd')}
        </Button>
      </Card>

      <div className="flex justify-end">
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>

      <Modal open={createOpen} title={t('customs.modal.create')} onClose={() => setCreateOpen(false)}>
        <div className="flex max-h-[70vh] flex-col gap-3 overflow-y-auto">
          <label className="text-sm text-muted" htmlFor="customs-create-name">
            {t('customs.field.name')}
          </label>
          <input
            id="customs-create-name"
            value={createSpec.name}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, name: e.target.value }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="customs-create-notes">
            {t('customs.field.notes')}
          </label>
          <textarea
            id="customs-create-notes"
            value={createSpec.notes}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, notes: e.target.value }))}
            rows={3}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />

          <label className="text-sm text-muted" htmlFor="customs-create-mode">
            {t('customs.field.mode')}
          </label>
          <Select
            id="customs-create-mode"
            value={createSpec.join_mode}
            onChange={(id) => setCreateSpec((prev) => ({ ...prev, join_mode: id as CreateSpec['join_mode'] }))}
            options={[
              { id: 'solo', name: t('customs.mode.solo') },
              { id: 'team_code', name: t('customs.mode.teamCode') },
            ]}
          />

          <label className="text-sm text-muted" htmlFor="customs-create-channel">
            {t('common.channel')}
          </label>
          <Select
            id="customs-create-channel"
            value={createSpec.channel_id}
            onChange={(id) => setCreateSpec((prev) => ({ ...prev, channel_id: id }))}
            options={channels}
            placeholder={t('common.selectChannel')}
          />

          <label className="text-sm text-muted" htmlFor="customs-create-ping">
            {t('customs.field.ping')}
          </label>
          <Select
            id="customs-create-ping"
            value={createSpec.ping}
            onChange={(id) => setCreateSpec((prev) => ({ ...prev, ping: id as CustomsPingMode }))}
            options={pingOptions(t)}
          />

          <label className="text-sm text-muted" htmlFor="customs-create-signup">
            {t('customs.field.signup')}
          </label>
          <input
            id="customs-create-signup"
            type="number"
            min={0}
            max={240}
            value={createSpec.signup_minutes}
            onChange={(e) => setCreateSpec((prev) => ({ ...prev, signup_minutes: Number(e.target.value) || 0 }))}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
          />

          {createError && <p className="text-sm text-danger">{createError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)} disabled={createBusy}>
              {t('common.cancel')}
            </Button>
            <Button variant="primary" onClick={publish} disabled={createBusy}>
              {createBusy ? t('common.creating') : t('customs.publish')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
