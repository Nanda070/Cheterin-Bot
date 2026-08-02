import { Gear, ListChecks, MaskHappy } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import {
  advanceMafiaGamePhase,
  endMafiaGame,
  fetchChannels,
  fetchMafiaGameDetail,
  fetchMafiaGames,
  fetchMafiaSettings,
  updateMafiaSettings,
  type ChannelInfo,
  type MafiaGameDetail,
  type MafiaGameSummary,
  type MafiaSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

type Tab = 'settings' | 'games'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function MafiaPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<MafiaSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [games, setGames] = useState<MafiaGameSummary[] | null>(null)
  const [detail, setDetail] = useState<MafiaGameDetail | null>(null)
  const [hostBusy, setHostBusy] = useState(false)

  const roleLabel = (role: string) => {
    const map: Record<string, string> = {
      mafia: t('mafia.role.mafia'),
      citizen: t('mafia.role.citizen'),
      doctor: t('mafia.role.doctor'),
      sheriff: t('mafia.role.sheriff'),
    }
    return map[role] ?? role
  }

  const tabs = useMemo(
    () =>
      [
        { key: 'settings' as const, label: t('common.settings'), icon: Gear },
        { key: 'games' as const, label: t('common.activeGames'), icon: ListChecks },
      ] as const,
    [t],
  )

  const phaseLabel = (phase: string) => {
    const map: Record<string, string> = {
      lobby: t('mafia.phase.lobby'),
      night: t('mafia.phase.night'),
      day_discussion: t('mafia.phase.dayDiscussion'),
      day_vote: t('mafia.phase.dayVote'),
      ended: t('mafia.phase.ended'),
    }
    return map[phase] ?? phase
  }

  useEffect(() => {
    Promise.all([fetchMafiaSettings(), fetchChannels()])
      .then(([s, ch]) => {
        setSettings(s)
        setChannels(ch)
      })
      .catch(() => setError(t('mafia.errorLoadSettings')))
  }, [t])

  useEffect(() => {
    if (tab !== 'games') return
    fetchMafiaGames()
      .then(setGames)
      .catch(() => setError(t('mafia.errorLoadGames')))
  }, [tab, t])

  const openDetail = (id: number) => {
    fetchMafiaGameDetail(id)
      .then(setDetail)
      .catch(() => setError(t('mafia.errorLoadGames')))
  }

  const closeDetail = () => setDetail(null)

  const refreshDetail = () => {
    if (detail) openDetail(detail.game.id)
  }

  const refreshGames = () => {
    fetchMafiaGames()
      .then(setGames)
      .catch(() => setError(t('mafia.errorLoadGames')))
  }

  const advancePhase = async () => {
    if (!detail) return
    setHostBusy(true)
    setError('')
    try {
      await advanceMafiaGamePhase(detail.game.id)
      refreshDetail()
      refreshGames()
    } catch (err) {
      setError(formatApiError(err, t, 'mafia.errorAdvance'))
    } finally {
      setHostBusy(false)
    }
  }

  const endGame = async () => {
    if (!detail) return
    if (!window.confirm(t('mafia.confirmEndBody'))) return
    setHostBusy(true)
    setError('')
    try {
      await endMafiaGame(detail.game.id)
      closeDetail()
      refreshGames()
    } catch (err) {
      setError(formatApiError(err, t, 'mafia.errorEnd'))
    } finally {
      setHostBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const patch = (updater: (prev: MafiaSettings) => MafiaSettings) => {
    setSettings((prev) => (prev ? updater(prev) : prev))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateMafiaSettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'mafia.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <MaskHappy size={22} className="text-primary" />
          {t('mafia.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('common.moduleEnabled') : t('common.moduleDisabled')}
        />
      </div>
      <p className="text-sm text-muted">{t('mafia.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-1 border-b border-border">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'settings' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('mafia.playersDefault')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-min-players">
                  {t('mafia.minPlayers')}
                </label>
                <input
                  id="mafia-min-players"
                  type="number"
                  min={5}
                  max={99}
                  value={settings.default_min_players}
                  onChange={(e) => patch((p) => ({ ...p, default_min_players: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-max-players">
                  {t('mafia.maxPlayers')}
                </label>
                <input
                  id="mafia-max-players"
                  type="number"
                  min={5}
                  max={99}
                  value={settings.default_max_players}
                  onChange={(e) => patch((p) => ({ ...p, default_max_players: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('mafia.timersDefault')}</h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-night-timer">
                  {t('mafia.timer.night')}
                </label>
                <input
                  id="mafia-night-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_night_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_night_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-discussion-timer">
                  {t('mafia.timer.discussion')}
                </label>
                <input
                  id="mafia-discussion-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_day_discussion_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_day_discussion_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-vote-timer">
                  {t('mafia.timer.vote')}
                </label>
                <input
                  id="mafia-vote-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_day_vote_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_day_vote_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('mafia.logs')}</h2>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="mafia-log-channel">
                {t('mafia.logChannel')}
              </label>
              <Select
                id="mafia-log-channel"
                value={settings.log_channel_id}
                onChange={(id) => patch((p) => ({ ...p, log_channel_id: id }))}
                options={channels}
                placeholder={t('common.notSet')}
              />
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

      {tab === 'games' && (
        <div className="flex flex-col gap-3">
          {!games && <p className="text-sm text-muted">{t('common.loading')}</p>}
          {games && games.length === 0 && <p className="text-sm text-muted">{t('common.noActiveGames')}</p>}
          {games?.map((game) => (
            <Card key={game.id} className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => (detail?.game.id === game.id ? closeDetail() : openDetail(game.id))}
                className="flex items-center justify-between gap-3 text-left"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {t('mafia.game', { id: game.id, channel: game.channel_name })}
                  </p>
                  <p className="text-xs text-muted">
                    {phaseLabel(game.phase)} ·{' '}
                    {t('game.roundAlive', {
                      round: game.round_number,
                      alive: game.alive_count,
                      total: game.player_count,
                    })}
                  </p>
                </div>
              </button>

              {detail && detail.game.id === game.id && (
                <div className="flex flex-col gap-4 border-t border-border pt-3">
                  {game.status === 'active' && (
                    <div>
                      <h3 className="mb-2 text-sm font-semibold text-foreground">{t('mafia.hostControls')}</h3>
                      <div className="flex gap-2">
                        <Button variant="secondary" onClick={advancePhase} disabled={hostBusy}>
                          {t('mafia.advancePhase')}
                        </Button>
                        <Button variant="danger" onClick={endGame} disabled={hostBusy}>
                          {t('mafia.endGame')}
                        </Button>
                      </div>
                    </div>
                  )}

                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-foreground">{t('mafia.roster')}</h3>
                    <div className="flex flex-col gap-1.5">
                      {detail.players.map((p) => (
                        <div
                          key={p.user_id}
                          className={`flex items-center justify-between gap-3 rounded-control border border-border px-3 py-2 text-sm ${
                            p.alive ? 'text-foreground' : 'text-muted line-through'
                          }`}
                        >
                          <div>
                            <span className="font-medium">{p.display_name}</span>
                            <span className="ml-2 text-xs text-muted">{t('mafia.roleLabel', { role: roleLabel(p.role) })}</span>
                          </div>
                          {(game.phase === 'night' || game.phase === 'day_vote') && p.alive && (
                            <span className={`text-xs ${p.action_submitted ? 'text-primary' : 'text-muted'}`}>
                              {p.action_submitted ? t('mafia.actionSubmitted') : t('mafia.actionPending')}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-foreground">{t('mafia.events')}</h3>
                    {detail.events.length === 0 && <p className="text-sm text-muted">{t('mafia.events.empty')}</p>}
                    <div className="flex flex-col gap-1.5">
                      {detail.events.map((e, idx) => (
                        <div key={idx} className="rounded-control border border-border px-3 py-2 text-sm text-foreground">
                          {e.payload || e.event_type}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
