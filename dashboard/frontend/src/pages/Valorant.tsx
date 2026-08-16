import { Crosshair } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchChannels, fetchPremierSettings, fetchRoles, fetchValorantCommands, fetchValorantPanels, updatePremierSettings, updateValorantCommands, updateValorantPanels, type ChannelInfo, type PremierSettings, type RoleInfo, type ValorantPanelCatalog, type ValorantPanelSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { CustomsPage } from './Customs'
import { ValCheckerPage } from './ValChecker'

type Tab = 'premier' | 'panels' | 'commands' | 'customs' | 'valchecker'

export function ValorantPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const initialTab: Tab = requestedTab === 'customs' || requestedTab === 'valchecker' || requestedTab === 'panels' || requestedTab === 'commands' ? requestedTab : 'premier'
  const [tab, setTab] = useState<Tab>(initialTab)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [premier, setPremier] = useState<PremierSettings | null>(null)
  const [panels, setPanels] = useState<ValorantPanelSettings | null>(null)
  const [catalog, setCatalog] = useState<ValorantPanelCatalog | null>(null)
  const [commandsEnabled, setCommandsEnabled] = useState(true)
  const [message, setMessage] = useState('')
  useEffect(() => setTab(initialTab), [initialTab])
  useEffect(() => {
    fetchChannels().then(setChannels).catch(() => setChannels([]))
    fetchRoles().then(setRoles).catch(() => setRoles([]))
    fetchPremierSettings().then(setPremier).catch(() => setMessage(t('valorant.errorLoad')))
    fetchValorantPanels().then(({ settings, catalog: data }) => { setPanels(settings); setCatalog(data) }).catch(() => setMessage(t('valorant.errorLoad')))
    fetchValorantCommands().then((data) => setCommandsEnabled(data.enabled)).catch(() => setMessage(t('valorant.errorLoad')))
  }, [t])
  if (!premier || !panels || !catalog) return <p className="text-sm text-muted">{message || t('common.loading')}</p>
  const savePremier = async () => { setPremier(await updatePremierSettings(premier)); setMessage(t('common.saved')) }
  const savePanels = async () => { const result = await updateValorantPanels(panels); setPanels(result.settings); setMessage(t('common.saved')) }
  const tabs: Tab[] = ['premier', 'panels', 'commands', 'customs', 'valchecker']
  const selectTab = (next: Tab) => {
    setTab(next)
    setSearchParams(next === 'premier' ? {} : { tab: next }, { replace: true })
  }
  return <div className="flex max-w-4xl flex-col gap-5">
    <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground"><Crosshair size={22} className="text-primary" />{t('valorant.title')}</h1>
    <div className="flex flex-wrap gap-2 border-b border-border">{tabs.map((item) => <button key={item} onClick={() => selectTab(item)} className={`px-3 py-2 text-sm ${tab === item ? 'border-b-2 border-primary text-foreground' : 'text-muted'}`}>{t(`valorant.tab.${item}`)}</button>)}</div>
    {message && <p className="text-sm text-primary">{message}</p>}
    {tab === 'premier' && <Card className="flex flex-col gap-3">
      <Toggle checked={premier.enabled} onChange={(enabled) => setPremier({ ...premier, enabled })} label={t('valorant.premierEnabled')} />
      <p className="text-sm text-muted">{t('valorant.premierHint')}</p>
      <Select id="valorant-premier-channel" value={premier.channel_id} onChange={(channel_id) => setPremier({ ...premier, channel_id })} options={channels} placeholder={t('common.selectChannel')} />
      <a className="text-sm text-primary underline" href={premier.faq_url} target="_blank" rel="noreferrer">{t('valorant.premierFaq')}</a>
      <Button onClick={() => void savePremier()}>{t('common.save')}</Button>
    </Card>}
    {tab === 'panels' && <Card className="flex flex-col gap-3">
      <Toggle checked={panels.enabled} onChange={(enabled) => setPanels({ ...panels, enabled })} label={t('valorant.panelsEnabled')} />
      <p className="text-sm text-muted">{t('valorant.panelsHint')}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {Object.entries(catalog.agent_classes).flatMap(([, agents]) => agents).map((agent) => <Select key={agent.key} id={`valorant-agent-${agent.key}`} value={panels.agent_roles[agent.key] || ''} onChange={(id) => setPanels({ ...panels, agent_roles: { ...panels.agent_roles, [agent.key]: id } })} options={roles} placeholder={agent.name} />)}
        {catalog.playstyles.map((item) => <Select key={item.key} id={`valorant-playstyle-${item.key}`} value={panels.playstyle_roles[item.key] || ''} onChange={(id) => setPanels({ ...panels, playstyle_roles: { ...panels.playstyle_roles, [item.key]: id } })} options={roles} placeholder={item.name} />)}
        {catalog.servers.map((item) => <Select key={item.key} id={`valorant-server-${item.key}`} value={panels.server_roles[item.key] || ''} onChange={(id) => setPanels({ ...panels, server_roles: { ...panels.server_roles, [item.key]: id } })} options={roles} placeholder={item.name} />)}
        {catalog.notifications.map((item) => <Select key={item.key} id={`valorant-notification-${item.key}`} value={panels.notification_roles[item.key] || ''} onChange={(id) => setPanels({ ...panels, notification_roles: { ...panels.notification_roles, [item.key]: id } })} options={roles} placeholder={item.name} />)}
      </div>
      <Button onClick={() => void savePanels()}>{t('common.save')}</Button>
    </Card>}
    {tab === 'commands' && <Card className="flex flex-col gap-3"><h2 className="font-semibold">{t('valorant.commandsTitle')}</h2><p className="text-sm text-muted">/valorant agent · buddy · map · skin · weapon</p><Toggle checked={commandsEnabled} onChange={async (enabled) => setCommandsEnabled((await updateValorantCommands(enabled)).enabled)} label={t('valorant.commandsEnabled')} /></Card>}
    {tab === 'customs' && <CustomsPage />}
    {tab === 'valchecker' && <ValCheckerPage />}
  </div>
}
