import { Gear, ListChecks, Vault } from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import { useEffect, useState } from 'react'
import {
  applyBunkerAbility,
  fetchBunkerCardPools,
  fetchBunkerGameDetail,
  fetchBunkerGames,
  fetchBunkerSettings,
  fetchChannels,
  patchBunkerPlayerCharacter,
  updateBunkerSettings,
  type BunkerCardPools,
  type BunkerCharacter,
  type BunkerGameDetail,
  type BunkerGameSummary,
  type BunkerSettings,
  type ChannelInfo,
} from '../api/client'
import { isBunkerHealthy } from '../config/bunkerMarkers'
import { BunkerCharacterEditor } from './BunkerCharacterEditor'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

type Tab = 'settings' | 'games'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function bunkerPhaseLabel(phase: string, t: (k: string) => string) {
  const m: Record<string, string> = {
    lobby: 'bunker.phase.lobby',
    discussion: 'bunker.phase.discussion',
    vote: 'bunker.phase.vote',
    ended: 'bunker.phase.ended',
  }
  return m[phase] ? t(m[phase]) : phase
}

function characterSummary(character: BunkerCharacter | null, t: (k: string) => string): string {
  if (!character) return '—'
  const parts: string[] = []
  if (character.profession) parts.push(`${character.profession.name} (${character.profession.experience_level})`)
  if (character.age) parts.push(character.age.label)
  if (character.gender) parts.push(character.gender)
  if (character.health) {
    parts.push(isBunkerHealthy(character.health) ? t('bunker.healthHealthy') : character.health.disease_name ?? character.health.severity)
  }
  return parts.join(', ') || '—'
}

export function BunkerPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<BunkerSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  const [games, setGames] = useState<BunkerGameSummary[] | null>(null)
  const [detail, setDetail] = useState<BunkerGameDetail | null>(null)
  const [cardPools, setCardPools] = useState<BunkerCardPools | null>(null)
  const [editingUserId, setEditingUserId] = useState<string | null>(null)
  const [editBusy, setEditBusy] = useState(false)
  const [editError, setEditError] = useState('')

  useEffect(() => {
    Promise.all([fetchBunkerSettings(), fetchChannels()])
      .then(([s, ch]) => {
        setSettings(s)
        setChannels(ch)
      })
      .catch(() => setError(t('bunker.errorLoadSettings')))
  }, [])

  useEffect(() => {
    if (tab !== 'games') return
    fetchBunkerGames()
      .then(setGames)
      .catch(() => setError(t('bunker.errorLoadGames')))
    if (!cardPools) {
      fetchBunkerCardPools()
        .then(setCardPools)
        .catch(() => setError(t('bunker.errorLoadPools')))
    }
  }, [tab, cardPools, t])

  const openDetail = (id: number) => {
    fetchBunkerGameDetail(id)
      .then(setDetail)
      .catch(() => setError(t('bunker.errorLoadGame')))
  }

  const closeDetail = () => setDetail(null)

  const refreshDetail = () => {
    if (detail) openDetail(detail.game.id)
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const patch = (updater: (prev: BunkerSettings) => BunkerSettings) => {
    setSettings((prev) => (prev ? updater(prev) : prev))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateBunkerSettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch {
      setError(t('bunker.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const openEditor = (userId: string) => {
    setEditError('')
    setEditingUserId(userId)
  }

  const saveEditor = async (character: BunkerCharacter) => {
    if (!editingUserId || !detail) return
    setEditBusy(true)
    setEditError('')
    try {
      await patchBunkerPlayerCharacter(detail.game.id, editingUserId, character)
      setEditingUserId(null)
      refreshDetail()
    } catch {
      setEditError(t('bunker.errorSaveCard'))
    } finally {
      setEditBusy(false)
    }
  }

  const apply = async (announcementId: number) => {
    if (!detail) return
    try {
      await applyBunkerAbility(detail.game.id, announcementId)
      refreshDetail()
    } catch {
      setError(t('bunker.errorApply'))
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Vault size={22} className="text-primary" />
          {t('bunker.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('common.moduleEnabled') : t('common.moduleDisabled')}
        />
      </div>
      <p className="text-sm text-muted">
{t('bunker.intro')}
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-1 border-b border-border">
        {[{ key: 'settings' as Tab, labelKey: 'common.settings', icon: Gear }, { key: 'games' as Tab, labelKey: 'common.activeGames', icon: ListChecks }].map(({ key, labelKey, icon: Icon }) => (
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
            <h2 className="font-semibold text-foreground">{t('bunker.playersDefault')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="bunker-min-players">
                  {t('bunker.minPlayers')}
                </label>
                <input
                  id="bunker-min-players"
                  type="number"
                  min={4}
                  max={20}
                  value={settings.default_min_players}
                  onChange={(e) => patch((p) => ({ ...p, default_min_players: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="bunker-max-players">
                  {t('bunker.maxPlayers')}
                </label>
                <input
                  id="bunker-max-players"
                  type="number"
                  min={4}
                  max={20}
                  value={settings.default_max_players}
                  onChange={(e) => patch((p) => ({ ...p, default_max_players: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('bunker.cardDeal')}</h2>
            <Toggle
              checked={settings.default_unique_cards}
              onChange={(v) => patch((p) => ({ ...p, default_unique_cards: v }))}
              label={settings.default_unique_cards ? t('bunker.uniqueCardsOn') : t('bunker.uniqueCardsOff')}
            />
            <p className="text-xs text-muted">
{t('bunker.uniqueCardsHint')}
            </p>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('bunker.timersDefault')}</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="bunker-discussion-timer">
                  {t('bunker.timer.discussion')}
                </label>
                <input
                  id="bunker-discussion-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_discussion_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_discussion_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="bunker-vote-timer">
                  {t('bunker.timer.vote')}
                </label>
                <input
                  id="bunker-vote-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_vote_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_vote_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('bunker.logs')}</h2>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="bunker-log-channel">
                {t('bunker.logChannel')}
              </label>
              <Select
                id="bunker-log-channel"
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
                    {t('bunker.game', { id: game.id, channel: game.channel_name })}
                  </p>
                  <p className="text-xs text-muted">
                    {t('bunker.gameMeta', {
                      phase: bunkerPhaseLabel(game.phase, t),
                      round: game.round_number,
                      alive: game.alive_count,
                      total: game.player_count,
                    })}
                    {game.bunker_capacity ? ` · ${t('bunker.capacity', { count: game.bunker_capacity })}` : ''}
                    {' · '}
                    {game.unique_cards ? t('bunker.uniqueCards') : t('bunker.duplicateCards')}
                  </p>
                </div>
              </button>

              {detail && detail.game.id === game.id && (
                <div className="flex flex-col gap-4 border-t border-border pt-3">
                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-foreground">{t('bunker.players')}</h3>
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
                            <span className="ml-2 text-xs text-muted">{characterSummary(p.character, t)}</span>
                          </div>
                          <Button variant="secondary" onClick={() => openEditor(p.user_id)}>
                            {t('common.edit')}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-foreground">{t('bunker.abilities')}</h3>
                    {detail.ability_announcements.length === 0 && (
                      <p className="text-sm text-muted">{t('bunker.abilities.empty')}</p>
                    )}
                    <div className="flex flex-col gap-1.5">
                      {detail.ability_announcements.map((a) => (
                        <div
                          key={a.id}
                          className="flex items-center justify-between gap-3 rounded-control border border-border px-3 py-2 text-sm"
                        >
                          <div>
                            <p className="text-foreground">
                              <span className="font-medium">{a.player_display_name}</span> — «{a.card_name}»
                              {a.target_display_name ? ` · ${t('bunker.editor.targetPlayer')}: ${a.target_display_name}` : ''}
                            </p>
                            {a.note && <p className="text-xs text-muted">{a.note}</p>}
                          </div>
                          {a.applied ? (
                            <span className="text-xs text-primary">{t('common.applied')}</span>
                          ) : (
                            <Button variant="primary" onClick={() => apply(a.id)}>
                              {t('bunker.apply')}
                            </Button>
                          )}
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

      <Modal open={editingUserId !== null} title={t('bunker.modal.editCard')} onClose={() => setEditingUserId(null)}>
        {editingUserId && detail && (() => {
          const player = detail.players.find((p) => p.user_id === editingUserId)
          if (!player) return null
          if (!cardPools) return <p className="text-sm text-muted">{t('bunker.modal.loadingPools')}</p>
          return (
            <div className="flex flex-col gap-3">
              <p className="text-xs text-muted">
{t('bunker.modal.editHint')}
              </p>
              <BunkerCharacterEditor
                character={player.character ?? {}}
                pools={cardPools}
                roster={detail.players.map((p) => ({ user_id: p.user_id, display_name: p.display_name }))}
                currentUserId={editingUserId}
                onSave={saveEditor}
                onCancel={() => setEditingUserId(null)}
                busy={editBusy}
              />
              {editError && <p className="text-sm text-danger">{editError}</p>}
            </div>
          )
        })()}
      </Modal>
    </div>
  )
}
