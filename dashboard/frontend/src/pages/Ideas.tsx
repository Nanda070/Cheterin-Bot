import { useEffect, useState } from 'react'
import { decideIdeaCase, fetchChannels, fetchIdeaCases, fetchIdeasSettings, updateIdeasSettings, type ChannelInfo, type IdeaCase, type IdeasSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

export function IdeasPage() {
  const t = useT()
  const [settings, setSettings] = useState<IdeasSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [cases, setCases] = useState<IdeaCase[]>([])
  const reload = () => fetchIdeaCases('pending').then(setCases).catch(() => setCases([]))
  useEffect(() => { fetchIdeasSettings().then(setSettings); fetchChannels().then(setChannels); reload() }, [])
  if (!settings) return <p className="text-sm text-muted">{t('common.loading')}</p>
  const save = async () => setSettings(await updateIdeasSettings(settings))
  const decide = async (caseId: string, approved: boolean) => { await decideIdeaCase(caseId, approved); reload() }
  return <div className="grid gap-4 lg:grid-cols-2">
    <Card className="flex flex-col gap-3">
      <h2 className="font-semibold">{t('ideas.title')}</h2>
      <Toggle checked={settings.enabled} onChange={(enabled) => setSettings({ ...settings, enabled })} label={t('ideas.enabled')} />
      <Select id="idea-intake" value={settings.intake_channel_id} onChange={(intake_channel_id) => setSettings({ ...settings, intake_channel_id })} options={channels} placeholder={t('ideas.intake')} />
      <Select id="idea-review" value={settings.review_channel_id} onChange={(review_channel_id) => setSettings({ ...settings, review_channel_id })} options={channels} placeholder={t('ideas.review')} />
      <Select id="idea-publish" value={settings.channel_id} onChange={(channel_id) => setSettings({ ...settings, channel_id })} options={channels} placeholder={t('ideas.publish')} />
      <textarea value={settings.prompt} onChange={(event) => setSettings({ ...settings, prompt: event.target.value })} className="rounded border border-border bg-background p-2 text-sm" />
      <Button onClick={() => void save()}>{t('common.save')}</Button>
    </Card>
    <Card><h2 className="mb-3 font-semibold">{t('ideas.queue')}</h2>{cases.length ? cases.map((item) => <div key={item.case_id} className="mb-3 border-b border-border pb-3"><p className="text-sm">{item.case_id} · {item.submitter_display}</p><p className="my-2 text-sm text-muted">{item.text}</p><Button onClick={() => void decide(item.case_id, true)}>{t('ideas.approve')}</Button> <Button variant="danger" onClick={() => void decide(item.case_id, false)}>{t('ideas.reject')}</Button></div>) : <p className="text-sm text-muted">{t('ideas.empty')}</p>}</Card>
  </div>
}
