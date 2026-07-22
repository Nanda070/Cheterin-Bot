import { ChartBar, Crown, Gear, IdentificationCard, Microphone, Star, Trash, UsersThree } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  deleteCardBg,
  fetchChannels,
  fetchRoles,
  fetchXpLeaderboard,
  fetchXpOverview,
  resetAllXp,
  resetMemberXp,
  setMemberXp,
  updateXpSettings,
  uploadCardBg,
  type ChannelInfo,
  type RoleInfo,
  type XpLeaderboardEntry,
  type XpLeaderboardPage,
  type XpSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { ChipPicker } from '../components/ChipPicker'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

type Tab = 'settings' | 'level-rewards' | 'voice-rewards' | 'card' | 'members'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

function minutesToParts(minutes: number): { weeks: number; days: number; hours: number } {
  const weeks = Math.floor(minutes / (7 * 24 * 60))
  const days = Math.floor((minutes % (7 * 24 * 60)) / (24 * 60))
  const hours = Math.floor((minutes % (24 * 60)) / 60)
  return { weeks, days, hours }
}

export function LevelsPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<XpSettings | null>(null)
  const [memberCount, setMemberCount] = useState(0)
  const [hasCardBg, setHasCardBg] = useState(false)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [newMultiplierUserId, setNewMultiplierUserId] = useState('')

  const [board, setBoard] = useState<XpLeaderboardPage | null>(null)
  const [boardPage, setBoardPage] = useState(1)
  const [boardSearch, setBoardSearch] = useState('')
  const [boardSearchDraft, setBoardSearchDraft] = useState('')
  const [editing, setEditing] = useState<XpLeaderboardEntry | null>(null)
  const [editXp, setEditXp] = useState('')
  const [confirmResetAll, setConfirmResetAll] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)

  const tabs = useMemo(
    (): { key: Tab; label: string; icon: typeof Gear }[] => [
      { key: 'settings', label: t('levels.tab.settings'), icon: Gear },
      { key: 'level-rewards', label: t('levels.tab.levelRewards'), icon: Star },
      { key: 'voice-rewards', label: t('levels.tab.voiceRewards'), icon: Microphone },
      { key: 'card', label: t('levels.tab.card'), icon: IdentificationCard },
      { key: 'members', label: t('levels.tab.members'), icon: UsersThree },
    ],
    [t],
  )

  const formatMinutes = (minutes: number): string => {
    const { weeks, days, hours } = minutesToParts(minutes)
    const parts: string[] = []
    if (weeks) parts.push(t('levels.time.weeks', { n: weeks }))
    if (days) parts.push(t('levels.time.days', { n: days }))
    if (hours) parts.push(t('levels.time.hours', { n: hours }))
    return parts.length ? parts.join(' ') : t('levels.time.minutes', { n: minutes })
  }

  const roleOptions = roles.map((r) => ({ id: r.id, name: r.name }))

  useEffect(() => {
    Promise.all([
      fetchXpOverview(),
      fetchChannels().catch(() => [] as ChannelInfo[]),
      fetchRoles().catch(() => [] as RoleInfo[]),
    ])
      .then(([overview, ch, rl]) => {
        setSettings(overview.settings)
        setMemberCount(overview.member_count)
        setHasCardBg(overview.has_card_bg)
        setChannels(ch)
        setRoles(rl)
      })
      .catch(() => setError(t('levels.errorLoadSettings')))
  }, [t])

  useEffect(() => {
    if (tab !== 'members') return
    fetchXpLeaderboard(boardPage, boardSearch)
      .then(setBoard)
      .catch(() => setError(t('levels.errorLoadLeaderboard')))
  }, [tab, boardPage, boardSearch, t])

  useEffect(() => {
    const timer = setTimeout(() => {
      setBoardPage(1)
      setBoardSearch(boardSearchDraft)
    }, 300)
    return () => clearTimeout(timer)
  }, [boardSearchDraft])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const patch = (updater: (prev: XpSettings) => XpSettings) => {
    setSettings((prev) => (prev ? updater(prev) : prev))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateXpSettings(settings)
      setSettings(updated.settings)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'levels.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const act = async (fn: () => Promise<unknown>, reload = false) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      if (reload && tab === 'members') {
        setBoard(await fetchXpLeaderboard(boardPage, boardSearch))
      }
    } catch (err) {
      setError(formatApiError(err, t, 'levels.errorOperation'))
    } finally {
      setBusy(false)
    }
  }

  const saveBar = (
    <div className="flex items-center gap-3">
      <Button variant="primary" onClick={save} disabled={busy}>
        {busy ? t('common.saving') : t('common.save')}
      </Button>
      {saved && <span className="text-sm text-primary">{saved}</span>}
    </div>
  )

  return (
    <div className="flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ChartBar size={22} className="text-primary" />
          {t('levels.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => patch((p) => ({ ...p, enabled: v }))}
          label={settings.enabled ? t('levels.moduleEnabled') : t('levels.moduleDisabled')}
        />
      </div>

      <nav className="flex flex-wrap gap-1 rounded-card border border-border bg-surface p-1.5">
        {tabs.map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 rounded-control px-3 py-1.5 text-sm transition-colors ${
              tab === key ? 'bg-primary-muted text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
            }`}
          >
            <TabIcon size={15} />
            {label}
          </button>
        ))}
      </nav>

      {error && <p className="text-sm text-danger">{error}</p>}

      {tab === 'settings' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('levels.general')}</h2>
            <Toggle
              checked={settings.public_leaderboard}
              onChange={(v) => patch((p) => ({ ...p, public_leaderboard: v }))}
              label={t('levels.publicLeaderboard')}
            />
            <Toggle
              checked={settings.reset_on_leave}
              onChange={(v) => patch((p) => ({ ...p, reset_on_leave: v }))}
              label={t('levels.resetOnLeave')}
            />
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('levels.textXp')}</h2>
              <Toggle
                checked={settings.text.enabled}
                onChange={(v) => patch((p) => ({ ...p, text: { ...p.text, enabled: v } }))}
              />
            </div>
            <p className="text-xs text-muted">{t('levels.textXpHint')}</p>
            <ChipPicker
              label={t('levels.ignoredRoles')}
              hint={t('levels.textIgnoredRolesHint')}
              options={roleOptions}
              selected={settings.text.ignored_roles}
              onChange={(ids) => patch((p) => ({ ...p, text: { ...p.text, ignored_roles: ids } }))}
            />
            <ChipPicker
              label={t('levels.targetChannels')}
              hint={t('levels.emptyMeansAll')}
              options={channels}
              selected={settings.text.target_channels}
              onChange={(ids) => patch((p) => ({ ...p, text: { ...p.text, target_channels: ids } }))}
            />
            <ChipPicker
              label={t('levels.ignoredChannels')}
              options={channels}
              selected={settings.text.ignored_channels}
              onChange={(ids) => patch((p) => ({ ...p, text: { ...p.text, ignored_channels: ids } }))}
            />
            <div className="flex items-center gap-3">
              <label className="text-sm text-muted" htmlFor="text-mult">
                {t('levels.textMultiplier', { percent: settings.text.multiplier })}
              </label>
              <input
                id="text-mult"
                type="range"
                min={0}
                max={300}
                step={5}
                value={settings.text.multiplier}
                onChange={(e) => patch((p) => ({ ...p, text: { ...p.text, multiplier: Number(e.target.value) } }))}
                className="flex-1 accent-[#5865f2]"
              />
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('levels.voiceXp')}</h2>
              <Toggle
                checked={settings.voice.enabled}
                onChange={(v) => patch((p) => ({ ...p, voice: { ...p.voice, enabled: v } }))}
              />
            </div>
            <p className="text-xs text-muted">{t('levels.voiceXpHint')}</p>
            <ChipPicker
              label={t('levels.ignoredRoles')}
              options={roleOptions}
              selected={settings.voice.ignored_roles}
              onChange={(ids) => patch((p) => ({ ...p, voice: { ...p.voice, ignored_roles: ids } }))}
            />
            <ChipPicker
              label={t('levels.targetChannels')}
              hint={t('levels.emptyMeansAllVoice')}
              options={channels}
              selected={settings.voice.target_channels}
              onChange={(ids) => patch((p) => ({ ...p, voice: { ...p.voice, target_channels: ids } }))}
            />
            <ChipPicker
              label={t('levels.ignoredChannels')}
              options={channels}
              selected={settings.voice.ignored_channels}
              onChange={(ids) => patch((p) => ({ ...p, voice: { ...p.voice, ignored_channels: ids } }))}
            />
            <div className="flex items-center gap-3">
              <label className="text-sm text-muted" htmlFor="voice-mult">
                {t('levels.voiceMultiplier', { percent: settings.voice.multiplier })}
              </label>
              <input
                id="voice-mult"
                type="range"
                min={0}
                max={300}
                step={5}
                value={settings.voice.multiplier}
                onChange={(e) => patch((p) => ({ ...p, voice: { ...p.voice, multiplier: Number(e.target.value) } }))}
                className="flex-1 accent-[#5865f2]"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="voice-max">
                {t('levels.voiceMaxCount')}
              </label>
              <input
                id="voice-max"
                type="number"
                min={0}
                max={99}
                value={settings.voice.max_count}
                onChange={(e) => patch((p) => ({ ...p, voice: { ...p.voice, max_count: Number(e.target.value) } }))}
                className={`${inputClass} w-32`}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="voice-base">
                {t('levels.voiceBasePerMinute')}
              </label>
              <input
                id="voice-base"
                type="number"
                min={1}
                max={100}
                value={settings.voice.base_per_minute}
                onChange={(e) => patch((p) => ({ ...p, voice: { ...p.voice, base_per_minute: Number(e.target.value) } }))}
                className={`${inputClass} w-32`}
              />
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted">{t('levels.memberMultipliersHint')}</p>
              {Object.entries(settings.voice.member_multipliers).map(([userId, mult]) => (
                <div key={userId} className="flex items-center gap-2">
                  <input value={userId} readOnly className={`${inputClass} w-52 opacity-70`} aria-label={t('levels.memberIdAria')} />
                  <input
                    type="number"
                    min={0}
                    max={1000}
                    value={mult}
                    aria-label={t('levels.memberMultiplierAria', { userId })}
                    onChange={(e) =>
                      patch((p) => ({
                        ...p,
                        voice: {
                          ...p.voice,
                          member_multipliers: { ...p.voice.member_multipliers, [userId]: Number(e.target.value) },
                        },
                      }))
                    }
                    className={`${inputClass} w-28`}
                  />
                  <Button
                    variant="secondary"
                    onClick={() =>
                      patch((p) => {
                        const next = { ...p.voice.member_multipliers }
                        delete next[userId]
                        return { ...p, voice: { ...p.voice, member_multipliers: next } }
                      })
                    }
                  >
                    {t('levels.remove')}
                  </Button>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <input
                  value={newMultiplierUserId}
                  onChange={(e) => setNewMultiplierUserId(e.target.value.trim())}
                  placeholder={t('levels.memberIdPlaceholder')}
                  className={`${inputClass} w-52`}
                />
                <Button
                  variant="secondary"
                  onClick={() => {
                    if (!/^\d+$/.test(newMultiplierUserId)) return
                    patch((p) => ({
                      ...p,
                      voice: {
                        ...p.voice,
                        member_multipliers: { ...p.voice.member_multipliers, [newMultiplierUserId]: 100 },
                      },
                    }))
                    setNewMultiplierUserId('')
                  }}
                >
                  {t('levels.addMember')}
                </Button>
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-foreground">{t('levels.levelUpAnnounce')}</h2>
              <Toggle
                checked={settings.announce.enabled}
                onChange={(v) => patch((p) => ({ ...p, announce: { ...p.announce, enabled: v } }))}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="announce-channel">
                {t('levels.announceChannel')}
              </label>
              <Select
                id="announce-channel"
                value={settings.announce.channel_id}
                onChange={(id) => patch((p) => ({ ...p, announce: { ...p.announce, channel_id: id } }))}
                options={channels}
                placeholder={t('levels.announceChannelPlaceholder')}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="announce-template">
                {t('levels.announceTemplate')}
              </label>
              <textarea
                id="announce-template"
                rows={3}
                value={settings.announce.template}
                onChange={(e) => patch((p) => ({ ...p, announce: { ...p.announce, template: e.target.value } }))}
                className={inputClass}
              />
              <span className="text-xs text-muted">{t('levels.announceTemplateVars')}</span>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="announce-delete">
                {t('levels.announceDeleteAfter')}
              </label>
              <input
                id="announce-delete"
                type="number"
                min={0}
                max={3600}
                value={settings.announce.delete_after}
                onChange={(e) =>
                  patch((p) => ({ ...p, announce: { ...p.announce, delete_after: Number(e.target.value) } }))
                }
                className={`${inputClass} w-32`}
              />
            </div>
          </Card>

          {saveBar}
        </div>
      )}

      {tab === 'level-rewards' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('levels.levelRewardsTitle')}</h2>
            {settings.level_rewards.length === 0 && <p className="text-sm text-muted">{t('levels.noRewards')}</p>}
            {settings.level_rewards.map((reward, index) => (
              <div key={index} className="flex flex-wrap items-end gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0">
                <div className="flex w-24 flex-col gap-1">
                  <label className="text-xs text-muted">{t('levels.level')}</label>
                  <input
                    type="number"
                    min={1}
                    max={999}
                    value={reward.level}
                    onChange={(e) =>
                      patch((p) => ({
                        ...p,
                        level_rewards: p.level_rewards.map((r, i) =>
                          i === index ? { ...r, level: Number(e.target.value) } : r,
                        ),
                      }))
                    }
                    className={inputClass}
                  />
                </div>
                <div className="min-w-60 flex-1">
                  <ChipPicker
                    label={t('levels.roles')}
                    options={roleOptions}
                    selected={reward.role_ids}
                    onChange={(ids) =>
                      patch((p) => ({
                        ...p,
                        level_rewards: p.level_rewards.map((r, i) => (i === index ? { ...r, role_ids: ids } : r)),
                      }))
                    }
                  />
                </div>
                <Button
                  variant="ghost"
                  onClick={() =>
                    patch((p) => ({ ...p, level_rewards: p.level_rewards.filter((_, i) => i !== index) }))
                  }
                >
                  <Trash size={16} />
                </Button>
              </div>
            ))}
            <div>
              <Button
                variant="secondary"
                onClick={() =>
                  patch((p) => ({ ...p, level_rewards: [...p.level_rewards, { level: 5, role_ids: [] }] }))
                }
              >
                {t('levels.addReward')}
              </Button>
            </div>
          </Card>
          {saveBar}
        </div>
      )}

      {tab === 'voice-rewards' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">{t('levels.voiceRewardsTitle')}</h2>
            {settings.voice_rewards.length === 0 && <p className="text-sm text-muted">{t('levels.noRewards')}</p>}
            {settings.voice_rewards.map((reward, index) => {
              const parts = minutesToParts(reward.minutes)
              const setParts = (weeks: number, days: number, hours: number) => {
                const minutes = Math.max(1, weeks * 7 * 24 * 60 + days * 24 * 60 + hours * 60)
                patch((p) => ({
                  ...p,
                  voice_rewards: p.voice_rewards.map((r, i) => (i === index ? { ...r, minutes } : r)),
                }))
              }
              return (
                <div key={index} className="flex flex-wrap items-end gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0">
                  <div className="flex gap-2">
                    {(['weeks', 'days', 'hours'] as const).map((unit) => (
                      <div key={unit} className="flex w-20 flex-col gap-1">
                        <label className="text-xs text-muted">
                          {unit === 'weeks' ? t('levels.weeks') : unit === 'days' ? t('levels.days') : t('levels.hours')}
                        </label>
                        <input
                          type="number"
                          min={0}
                          value={parts[unit]}
                          onChange={(e) => {
                            const v = Math.max(0, Number(e.target.value))
                            setParts(
                              unit === 'weeks' ? v : parts.weeks,
                              unit === 'days' ? v : parts.days,
                              unit === 'hours' ? v : parts.hours,
                            )
                          }}
                          className={inputClass}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="min-w-60 flex-1">
                    <ChipPicker
                      label={t('levels.rolesThreshold', { threshold: formatMinutes(reward.minutes) })}
                      options={roleOptions}
                      selected={reward.role_ids}
                      onChange={(ids) =>
                        patch((p) => ({
                          ...p,
                          voice_rewards: p.voice_rewards.map((r, i) => (i === index ? { ...r, role_ids: ids } : r)),
                        }))
                      }
                    />
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() =>
                      patch((p) => ({ ...p, voice_rewards: p.voice_rewards.filter((_, i) => i !== index) }))
                    }
                  >
                    <Trash size={16} />
                  </Button>
                </div>
              )
            })}
            <div>
              <Button
                variant="secondary"
                onClick={() =>
                  patch((p) => ({
                    ...p,
                    voice_rewards: [...p.voice_rewards, { minutes: 7 * 24 * 60, role_ids: [] }],
                  }))
                }
              >
                {t('levels.addReward')}
              </Button>
            </div>
          </Card>
          {saveBar}
        </div>
      )}

      {tab === 'card' && (
        <Card className="flex flex-col gap-4">
          <h2 className="font-semibold text-foreground">{t('levels.cardBgTitle')}</h2>
          <p className="text-sm text-muted">
            {t('levels.cardBgHint', {
              status: hasCardBg ? t('levels.cardBgCustom') : t('levels.cardBgDefault'),
            })}
          </p>
          <input
            ref={fileInput}
            type="file"
            accept="image/png,image/jpeg"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) {
                act(async () => {
                  await uploadCardBg(file)
                  setHasCardBg(true)
                  setSaved(t('levels.bgUploaded'))
                })
              }
              e.target.value = ''
            }}
          />
          <div className="flex gap-2">
            <Button variant="primary" onClick={() => fileInput.current?.click()} disabled={busy}>
              {t('levels.uploadBg')}
            </Button>
            {hasCardBg && (
              <Button
                variant="danger"
                onClick={() =>
                  act(async () => {
                    await deleteCardBg()
                    setHasCardBg(false)
                    setSaved(t('levels.bgDeleted'))
                  })
                }
                disabled={busy}
              >
                {t('levels.deleteBg')}
              </Button>
            )}
          </div>
          {saved && <p className="text-sm text-primary">{saved}</p>}
        </Card>
      )}

      {tab === 'members' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted">
              {t('levels.membersInList', { count: board?.total ?? memberCount })}
            </p>
            <Button variant="danger" onClick={() => setConfirmResetAll(true)} disabled={busy}>
              {t('levels.resetAllRating')}
            </Button>
          </div>
          <input
            value={boardSearchDraft}
            onChange={(e) => setBoardSearchDraft(e.target.value)}
            placeholder={t('levels.searchMember')}
            className={inputClass}
          />

          <Card className="p-0">
            {!board && <p className="p-4 text-sm text-muted">{t('common.loading')}</p>}
            {board && board.entries.length === 0 && <p className="p-4 text-sm text-muted">{t('levels.leaderboardEmpty')}</p>}
            {board?.entries.map((entry) => (
              <div
                key={entry.user_id}
                className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-2.5 last:border-b-0"
              >
                <span className="w-10 text-sm font-medium text-muted">#{entry.rank}</span>
                {entry.avatar ? (
                  <img src={entry.avatar} alt="" className="h-8 w-8 rounded-full" />
                ) : (
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-muted text-xs font-semibold text-primary">
                    {entry.display.slice(0, 1).toUpperCase()}
                  </span>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-foreground">
                    {entry.display}
                    {!entry.on_server && <span className="ml-2 text-xs text-muted">{t('levels.leftServer')}</span>}
                  </p>
                  <p className="text-xs text-muted">
                    {t('levels.memberStats', {
                      level: entry.level,
                      xp: entry.xp,
                      voiceTime: entry.voice_time_text,
                      messages: entry.messages,
                    })}
                  </p>
                </div>
                <div className="flex gap-1.5">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setEditing(entry)
                      setEditXp(String(entry.xp))
                    }}
                  >
                    {t('levels.editXp')}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => act(() => resetMemberXp(entry.user_id), true)}
                    disabled={busy}
                  >
                    {t('levels.reset')}
                  </Button>
                </div>
              </div>
            ))}
          </Card>

          {board && board.total > board.page_size && (
            <div className="flex items-center justify-center gap-3">
              <Button variant="ghost" disabled={boardPage <= 1} onClick={() => setBoardPage((p) => p - 1)}>
                {t('levels.prevPage')}
              </Button>
              <span className="text-sm text-muted">
                {t('levels.pageOf', { page: board.page, total: Math.ceil(board.total / board.page_size) })}
              </span>
              <Button
                variant="ghost"
                disabled={boardPage >= Math.ceil(board.total / board.page_size)}
                onClick={() => setBoardPage((p) => p + 1)}
              >
                {t('levels.nextPage')}
              </Button>
            </div>
          )}
        </div>
      )}

      <Modal open={editing !== null} title={t('levels.editXpTitle', { display: editing?.display ?? '' })} onClose={() => setEditing(null)}>
        <div className="flex flex-col gap-3">
          <input
            type="number"
            min={0}
            value={editXp}
            onChange={(e) => setEditXp(e.target.value)}
            className={inputClass}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setEditing(null)} disabled={busy}>
              {t('levels.cancel')}
            </Button>
            <Button
              variant="primary"
              disabled={busy}
              onClick={() =>
                act(async () => {
                  if (editing) await setMemberXp(editing.user_id, Math.max(0, Number(editXp)))
                  setEditing(null)
                }, true)
              }
            >
              {t('common.save')}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal open={confirmResetAll} title={t('levels.resetAllTitle')} onClose={() => setConfirmResetAll(false)}>
        <p className="mb-4 text-sm text-muted">{t('levels.resetAllWarning')}</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmResetAll(false)} disabled={busy}>
            {t('levels.cancel')}
          </Button>
          <Button
            variant="danger"
            disabled={busy}
            onClick={() =>
              act(async () => {
                await resetAllXp()
                setConfirmResetAll(false)
              }, true)
            }
          >
            <Crown size={16} />
            {t('levels.resetAllConfirm')}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
