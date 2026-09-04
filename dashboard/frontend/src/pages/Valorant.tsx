import { Crosshair } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  fetchChannels,
  fetchPremierSettings,
  fetchRoles,
  fetchValorantCommands,
  fetchValorantPanels,
  publishValorantPanel,
  updatePremierSettings,
  updateValorantCommands,
  updateValorantPanels,
  type ChannelInfo,
  type PremierSettings,
  type RoleInfo,
  type ValorantPanelCatalog,
  type ValorantPanelSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { CustomsPage } from './Customs'
import { ValCheckerPage } from './ValChecker'

type Tab = 'premier' | 'panels' | 'commands' | 'customs' | 'valchecker'

const PANEL_KINDS = ['agents', 'playstyles', 'notifications', 'servers'] as const

function resolveTab(raw: string | null): Tab {
  if (raw === 'customs' || raw === 'valchecker' || raw === 'panels' || raw === 'commands' || raw === 'premier') {
    return raw
  }
  return 'premier'
}

export function ValorantPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const initialTab = resolveTab(requestedTab)
  const [tab, setTab] = useState<Tab>(initialTab)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [premier, setPremier] = useState<PremierSettings | null>(null)
  const [panels, setPanels] = useState<ValorantPanelSettings | null>(null)
  const [catalog, setCatalog] = useState<ValorantPanelCatalog | null>(null)
  const [commandsEnabled, setCommandsEnabled] = useState(true)
  const [publishChannelId, setPublishChannelId] = useState('')
  const [publishKind, setPublishKind] = useState<(typeof PANEL_KINDS)[number]>('agents')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => setTab(initialTab), [initialTab])

  useEffect(() => {
    if (!requestedTab) {
      setSearchParams({}, { replace: true })
      return
    }
    const resolved = resolveTab(requestedTab)
    if (requestedTab !== resolved) {
      setSearchParams(resolved === 'premier' ? {} : { tab: resolved }, { replace: true })
    }
  }, [requestedTab, setSearchParams])

  useEffect(() => {
    let cancelled = false
    setError('')
    Promise.all([
      fetchChannels().catch(() => [] as ChannelInfo[]),
      fetchRoles().catch(() => [] as RoleInfo[]),
      fetchPremierSettings(),
      fetchValorantPanels(),
      fetchValorantCommands(),
    ])
      .then(([ch, roleList, premierData, panelData, commandsData]) => {
        if (cancelled) return
        setChannels(ch)
        setRoles(roleList)
        setPremier(premierData)
        setPanels(panelData.settings)
        setCatalog(panelData.catalog)
        setCommandsEnabled(commandsData.enabled)
      })
      .catch((err) => {
        if (!cancelled) setError(formatApiError(err, t, 'valorant.errorLoad'))
      })
    return () => {
      cancelled = true
    }
  }, [t])

  const selectTab = (next: Tab) => {
    setTab(next)
    setSearchParams(next === 'premier' ? {} : { tab: next }, { replace: true })
  }

  const savePremier = async () => {
    if (!premier) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      setPremier(await updatePremierSettings(premier))
      setMessage(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'valorant.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const savePanels = async () => {
    if (!panels) return
    setBusy(true)
    setError('')
    setMessage('')
    try {
      const result = await updateValorantPanels(panels)
      setPanels(result.settings)
      setMessage(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'valorant.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const publishPanel = async () => {
    if (!publishChannelId) {
      setError(t('valorant.publishNeedChannel'))
      return
    }
    setBusy(true)
    setError('')
    setMessage('')
    try {
      await publishValorantPanel(publishKind, publishChannelId)
      setMessage(t('valorant.publishOk'))
    } catch (err) {
      setError(formatApiError(err, t, 'valorant.errorPublish'))
    } finally {
      setBusy(false)
    }
  }

  const tabs: Tab[] = ['premier', 'panels', 'commands', 'customs', 'valchecker']

  if (!premier || !panels || !catalog) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-5xl flex-col gap-5">
      <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <Crosshair size={22} className="text-primary" />
        {t('valorant.title')}
      </h1>
      <div className="flex flex-wrap gap-2 border-b border-border">
        {tabs.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => selectTab(item)}
            className={`px-3 py-2 text-sm ${
              tab === item ? 'border-b-2 border-primary text-foreground' : 'text-muted'
            }`}
          >
            {t(`valorant.tab.${item}`)}
          </button>
        ))}
      </div>

      {(message || error) && (
        <p className={`text-sm ${error ? 'text-danger' : 'text-primary'}`}>{error || message}</p>
      )}

      {tab === 'premier' && (
        <Card className="flex flex-col gap-3">
          <Toggle
            checked={premier.enabled}
            onChange={(enabled) => setPremier({ ...premier, enabled })}
            label={t('valorant.premierEnabled')}
          />
          <p className="text-sm text-muted">{t('valorant.premierHint')}</p>
          <Select
            id="valorant-premier-channel"
            value={premier.channel_id}
            onChange={(channel_id) => setPremier({ ...premier, channel_id })}
            options={channels}
            placeholder={t('common.selectChannel')}
          />
          <a className="text-sm text-primary underline" href={premier.faq_url} target="_blank" rel="noreferrer">
            {t('valorant.premierFaq')}
          </a>
          <p className="text-sm text-muted">
            {t('valorant.ideasHint')}{' '}
            <Link to="/feedback?tab=ideas" className="text-primary underline">
              {t('valorant.openIdeas')}
            </Link>
          </p>
          <Button onClick={() => void savePremier()} disabled={busy}>
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </Card>
      )}

      {tab === 'panels' && (
        <Card className="flex flex-col gap-3">
          <Toggle
            checked={panels.enabled}
            onChange={(enabled) => setPanels({ ...panels, enabled })}
            label={t('valorant.panelsEnabled')}
          />
          <p className="text-sm text-muted">{t('valorant.panelsHint')}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(catalog.agent_classes)
              .flatMap(([, agents]) => agents)
              .map((agent) => (
                <Select
                  key={agent.key}
                  id={`valorant-agent-${agent.key}`}
                  value={panels.agent_roles[agent.key] || ''}
                  onChange={(id) =>
                    setPanels({
                      ...panels,
                      agent_roles: { ...panels.agent_roles, [agent.key]: id },
                    })
                  }
                  options={roles}
                  kind="role"
                  placeholder={agent.name}
                />
              ))}
            {catalog.playstyles.map((item) => (
              <Select
                key={item.key}
                id={`valorant-playstyle-${item.key}`}
                value={panels.playstyle_roles[item.key] || ''}
                onChange={(id) =>
                  setPanels({
                    ...panels,
                    playstyle_roles: { ...panels.playstyle_roles, [item.key]: id },
                  })
                }
                options={roles}
                kind="role"
                placeholder={item.name}
              />
            ))}
            {catalog.servers.map((item) => (
              <Select
                key={item.key}
                id={`valorant-server-${item.key}`}
                value={panels.server_roles[item.key] || ''}
                onChange={(id) =>
                  setPanels({
                    ...panels,
                    server_roles: { ...panels.server_roles, [item.key]: id },
                  })
                }
                options={roles}
                kind="role"
                placeholder={item.name}
              />
            ))}
            {catalog.notifications.map((item) => (
              <Select
                key={item.key}
                id={`valorant-notification-${item.key}`}
                value={panels.notification_roles[item.key] || ''}
                onChange={(id) =>
                  setPanels({
                    ...panels,
                    notification_roles: { ...panels.notification_roles, [item.key]: id },
                  })
                }
                options={roles}
                kind="role"
                placeholder={item.name}
              />
            ))}
          </div>
          <div className="mt-2 flex flex-col gap-2 border-t border-border pt-3">
            <h3 className="text-sm font-medium text-foreground">{t('valorant.publishTitle')}</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <Select
                id="valorant-publish-channel"
                value={publishChannelId}
                onChange={setPublishChannelId}
                options={channels}
                placeholder={t('common.selectChannel')}
              />
              <Select
                id="valorant-publish-kind"
                value={publishKind}
                onChange={(id) => setPublishKind(id as (typeof PANEL_KINDS)[number])}
                options={PANEL_KINDS.map((kind) => ({
                  id: kind,
                  name: t(`valorant.publishKind.${kind}`),
                }))}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => void savePanels()} disabled={busy}>
                {busy ? t('common.saving') : t('common.save')}
              </Button>
              <Button variant="secondary" onClick={() => void publishPanel()} disabled={busy}>
                {t('valorant.publish')}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {tab === 'commands' && (
        <Card className="flex flex-col gap-3">
          <h2 className="font-semibold">{t('valorant.commandsTitle')}</h2>
          <p className="text-sm text-muted">/valorant agent · buddy · map · skin · weapon</p>
          <Toggle
            checked={commandsEnabled}
            onChange={async (enabled) => {
              try {
                setCommandsEnabled((await updateValorantCommands(enabled)).enabled)
                setMessage(t('common.saved'))
              } catch (err) {
                setError(formatApiError(err, t, 'valorant.errorSave'))
              }
            }}
            label={t('valorant.commandsEnabled')}
          />
        </Card>
      )}

      {tab === 'customs' && <CustomsPage />}
      {tab === 'valchecker' && <ValCheckerPage />}
    </div>
  )
}
