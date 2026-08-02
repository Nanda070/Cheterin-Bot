import { Heart, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  fetchChannels,
  fetchRelations,
  fetchRelationsMarriages,
  fetchRelationsTop,
  fetchRoles,
  updateRelations,
  type ChannelInfo,
  type RelationsAction,
  type RelationsMarriageRow,
  type RelationsPairRow,
  type RelationsSettings,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

type Tab = 'general' | 'actions' | 'levels' | 'roles' | 'romance' | 'top'

function parseTab(raw: string | null): Tab {
  if (
    raw === 'actions' ||
    raw === 'levels' ||
    raw === 'roles' ||
    raw === 'romance' ||
    raw === 'top'
  ) {
    return raw
  }
  return 'general'
}

function TabBar({ tab, setTab, t }: { tab: Tab; setTab: (t: Tab) => void; t: (k: string) => string }) {
  const tabs: { key: Tab; labelKey: string }[] = [
    { key: 'general', labelKey: 'relations.tab.general' },
    { key: 'actions', labelKey: 'relations.tab.actions' },
    { key: 'levels', labelKey: 'relations.tab.levels' },
    { key: 'roles', labelKey: 'relations.tab.roles' },
    { key: 'romance', labelKey: 'relations.tab.romance' },
    { key: 'top', labelKey: 'relations.tab.top' },
  ]
  return (
    <div className="flex flex-wrap gap-1 border-b border-border">
      {tabs.map(({ key, labelKey }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

function newAction(): RelationsAction {
  return {
    id: `action${Math.random().toString(36).slice(2, 7)}`,
    emoji: '❤️',
    hp_gain: 10,
    cooldown_sec: 60,
    enabled: true,
  }
}

function daysSince(ts: number): number {
  return Math.max(0, Math.floor((Date.now() / 1000 - ts) / 86400))
}

export function RelationsPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = parseTab(searchParams.get('tab'))
  const setTab = (next: Tab) => {
    if (next === 'general') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  const [settings, setSettings] = useState<RelationsSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [top, setTop] = useState<RelationsPairRow[]>([])
  const [marriages, setMarriages] = useState<RelationsMarriageRow[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    Promise.all([fetchRelations(), fetchChannels(), fetchRoles()])
      .then(([data, ch, r]) => {
        setSettings(data)
        setChannels(ch)
        setRoles(r)
      })
      .catch((err) => setError(formatApiError(err, t, 'relations.errorLoad')))
  }, [t])

  useEffect(() => {
    if (tab !== 'top') return
    Promise.all([fetchRelationsTop(15), fetchRelationsMarriages(15)])
      .then(([pairs, m]) => {
        setTop(pairs)
        setMarriages(m)
      })
      .catch(() => {
        setTop([])
        setMarriages([])
      })
  }, [tab])

  const save = async () => {
    if (!settings) return
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateRelations(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'relations.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const patchAction = (index: number, patch: Partial<RelationsAction>) => {
    setSettings({
      ...settings,
      actions: settings.actions.map((a, i) => (i === index ? { ...a, ...patch } : a)),
    })
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <Heart size={22} className="text-primary" weight="fill" />
            {t('relations.title')}
          </h1>
          <p className="mt-1 text-sm text-muted">{t('relations.intro')}</p>
        </div>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('relations.moduleOn') : t('relations.moduleOff')}
        />
      </div>

      <TabBar tab={tab} setTab={setTab} t={t} />

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      {tab === 'general' && (
        <Card className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">{t('relations.announceChannel')}</label>
            <Select
              value={settings.announce_channel_id}
              onChange={(id) => setSettings({ ...settings, announce_channel_id: id })}
              options={channels}
              placeholder={t('relations.channelPlaceholder')}
            />
            <span className="text-xs text-muted">{t('relations.announceHint')}</span>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="rel-max-day">
              {t('relations.maxPerDay')}
            </label>
            <input
              id="rel-max-day"
              type="number"
              min={1}
              max={500}
              value={settings.max_actions_per_day}
              onChange={(e) =>
                setSettings({ ...settings, max_actions_per_day: Number(e.target.value) })
              }
              className={`${inputClass} max-w-[12rem]`}
            />
          </div>
          <p className="text-xs text-muted">{t('relations.commandsHint')}</p>
        </Card>
      )}

      {tab === 'actions' && (
        <div className="flex flex-col gap-3">
          {settings.actions.map((action, index) => (
            <Card key={`${action.id}-${index}`} className="flex flex-col gap-3">
              <div className="flex items-center justify-between gap-2">
                <Toggle
                  checked={action.enabled}
                  onChange={(v) => patchAction(index, { enabled: v })}
                  label={action.enabled ? t('relations.actionOn') : t('relations.actionOff')}
                />
                <button
                  type="button"
                  className="text-muted hover:text-danger"
                  aria-label={t('relations.deleteAction')}
                  onClick={() =>
                    setSettings({
                      ...settings,
                      actions: settings.actions.filter((_, i) => i !== index),
                    })
                  }
                >
                  <Trash size={18} />
                </button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-muted">{t('relations.actionId')}</label>
                  <input
                    value={action.id}
                    onChange={(e) =>
                      patchAction(index, {
                        id: e.target.value.replace(/[^a-z0-9_-]/gi, '').toLowerCase().slice(0, 32),
                      })
                    }
                    className={inputClass}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-muted">{t('relations.actionEmoji')}</label>
                  <input
                    value={action.emoji}
                    onChange={(e) => patchAction(index, { emoji: e.target.value })}
                    className={inputClass}
                    maxLength={32}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-muted">{t('relations.actionHp')}</label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={action.hp_gain}
                    onChange={(e) => patchAction(index, { hp_gain: Number(e.target.value) })}
                    className={inputClass}
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-muted">{t('relations.actionCooldown')}</label>
                  <input
                    type="number"
                    min={0}
                    max={86400}
                    value={action.cooldown_sec}
                    onChange={(e) => patchAction(index, { cooldown_sec: Number(e.target.value) })}
                    className={inputClass}
                  />
                </div>
              </div>
            </Card>
          ))}
          <Button
            variant="secondary"
            onClick={() => setSettings({ ...settings, actions: [...settings.actions, newAction()] })}
            disabled={settings.actions.length >= 20}
          >
            <Plus size={16} />
            {t('relations.addAction')}
          </Button>
          <p className="text-xs text-muted">{t('relations.actionsSlashHint')}</p>
        </div>
      )}

      {tab === 'levels' && (
        <Card className="flex flex-col gap-3">
          <p className="text-sm text-muted">{t('relations.levelsIntro')}</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {settings.level_thresholds.map((thr, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-16 shrink-0 text-sm text-muted">
                  {t('relations.levelN', { n: i + 1 })}
                </span>
                <input
                  type="number"
                  min={0}
                  value={thr}
                  onChange={(e) => {
                    const next = [...settings.level_thresholds]
                    next[i] = Number(e.target.value)
                    setSettings({ ...settings, level_thresholds: next })
                  }}
                  className={inputClass}
                />
              </div>
            ))}
          </div>
        </Card>
      )}

      {tab === 'roles' && (
        <Card className="flex flex-col gap-3">
          <p className="text-sm text-muted">{t('relations.rolesIntro')}</p>
          {Array.from({ length: 11 }, (_, i) => i + 1).map((lvl) => (
            <div key={lvl} className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
              <span className="w-24 shrink-0 text-sm text-muted">
                {t('relations.levelN', { n: lvl })}
              </span>
              <Select
                value={settings.reward_roles[String(lvl)] || ''}
                onChange={(id) => {
                  const next = { ...settings.reward_roles }
                  if (!id) delete next[String(lvl)]
                  else next[String(lvl)] = id
                  setSettings({ ...settings, reward_roles: next })
                }}
                options={[{ id: '', name: t('relations.noRole') }, ...roles]}
                kind="role"
                placeholder={t('relations.pickRole')}
              />
            </div>
          ))}
        </Card>
      )}

      {tab === 'romance' && (
        <Card className="flex flex-col gap-4">
          <Toggle
            checked={settings.marriage_enabled}
            onChange={(v) => setSettings({ ...settings, marriage_enabled: v })}
            label={
              settings.marriage_enabled
                ? t('relations.romance.enabledOn')
                : t('relations.romance.enabledOff')
            }
          />
          <p className="text-xs text-muted">{t('relations.romance.commandsHint')}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="rel-min-marry">
                {t('relations.romance.minLevel')}
              </label>
              <input
                id="rel-min-marry"
                type="number"
                min={1}
                max={11}
                value={settings.min_level_to_marry}
                onChange={(e) =>
                  setSettings({ ...settings, min_level_to_marry: Number(e.target.value) })
                }
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="rel-proposal-to">
                {t('relations.romance.proposalTimeout')}
              </label>
              <input
                id="rel-proposal-to"
                type="number"
                min={60}
                max={3600}
                value={settings.proposal_timeout_sec}
                onChange={(e) =>
                  setSettings({ ...settings, proposal_timeout_sec: Number(e.target.value) })
                }
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="rel-bonus">
                {t('relations.romance.hpBonus')}
              </label>
              <input
                id="rel-bonus"
                type="number"
                min={0}
                max={200}
                value={settings.married_hp_bonus_percent}
                onChange={(e) =>
                  setSettings({ ...settings, married_hp_bonus_percent: Number(e.target.value) })
                }
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="rel-date-hp">
                {t('relations.romance.dateHp')}
              </label>
              <input
                id="rel-date-hp"
                type="number"
                min={1}
                max={500}
                value={settings.date_hp_gain}
                onChange={(e) =>
                  setSettings({ ...settings, date_hp_gain: Number(e.target.value) })
                }
                className={inputClass}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="rel-date-cd">
                {t('relations.romance.dateCooldown')}
              </label>
              <input
                id="rel-date-cd"
                type="number"
                min={0}
                max={86400}
                value={settings.date_cooldown_sec}
                onChange={(e) =>
                  setSettings({ ...settings, date_cooldown_sec: Number(e.target.value) })
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted">{t('relations.romance.marriedRole')}</label>
            <Select
              value={settings.married_role_id}
              onChange={(id) => setSettings({ ...settings, married_role_id: id })}
              options={[{ id: '', name: t('relations.noRole') }, ...roles]}
              kind="role"
              placeholder={t('relations.pickRole')}
            />
          </div>
          <Toggle
            checked={settings.divorce_requires_accept}
            onChange={(v) => setSettings({ ...settings, divorce_requires_accept: v })}
            label={t('relations.romance.divorceMutual')}
          />
          <Toggle
            checked={settings.allow_polygamy}
            onChange={(v) => setSettings({ ...settings, allow_polygamy: v })}
            label={t('relations.romance.polygamy')}
          />
        </Card>
      )}

      {tab === 'top' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-foreground">{t('relations.top.pairs')}</h2>
            {top.length === 0 ? (
              <p className="text-sm text-muted">{t('relations.topEmpty')}</p>
            ) : (
              top.map((row, i) => (
                <p key={`${row.user_a}-${row.user_b}`} className="text-sm text-foreground">
                  <span className="text-muted">#{i + 1}</span>{' '}
                  <code className="text-xs">{row.user_a}</code> ×{' '}
                  <code className="text-xs">{row.user_b}</code> —{' '}
                  {t('relations.topRow', { level: row.level, hp: row.hp })}
                </p>
              ))
            )}
          </Card>
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-foreground">{t('relations.top.marriages')}</h2>
            {marriages.length === 0 ? (
              <p className="text-sm text-muted">{t('relations.topMarriagesEmpty')}</p>
            ) : (
              marriages.map((row, i) => (
                <p key={`m-${row.user_a}-${row.user_b}`} className="text-sm text-foreground">
                  <span className="text-muted">#{i + 1}</span>{' '}
                  <code className="text-xs">{row.user_a}</code> ×{' '}
                  <code className="text-xs">{row.user_b}</code> —{' '}
                  {t('relations.topMarriageRow', {
                    days: daysSince(row.married_at),
                    level: row.level,
                    hp: row.hp,
                  })}
                </p>
              ))
            )}
          </Card>
        </div>
      )}

      {tab !== 'top' && (
        <div>
          <Button variant="primary" onClick={save} disabled={busy}>
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      )}
    </div>
  )
}
