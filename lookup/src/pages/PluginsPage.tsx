import { useEffect, useState } from 'react'
import { lookupFetch, type PluginEntry } from '../api/client'
import { EmptyState, LoadingBlock, PageHeader, Panel } from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'

export function PluginsPage() {
  const t = useT()
  const { lang } = useLanguage()
  const [plugins, setPlugins] = useState<PluginEntry[] | null>(null)

  useEffect(() => {
    void lookupFetch<{ plugins: PluginEntry[] }>('/plugins')
      .then((res) => setPlugins(res.plugins))
      .catch(() => setPlugins([]))
  }, [])

  return (
    <div className="space-y-7 lookup-rise">
      <PageHeader title={t('plugins.title')} lead={t('plugins.lead')} />

      {plugins == null ? <LoadingBlock rows={3} /> : null}

      {plugins && plugins.length === 0 ? (
        <EmptyState title={t('plugins.title')} body={t('plugins.empty')} />
      ) : null}

      {plugins && plugins.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {plugins.map((plugin) => (
            <Panel key={plugin.id} className="lookup-card-lift flex flex-col p-5 sm:p-6">
              <h2 className="font-display text-lg font-semibold">{plugin.name}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">
                {lang === 'ru' && plugin.description_ru ? plugin.description_ru : plugin.description}
              </p>
              <a
                href={plugin.url}
                target="_blank"
                rel="noreferrer"
                className="mt-5 inline-flex text-sm font-semibold text-primary-hover hover:underline"
              >
                {t('plugins.open')} →
              </a>
            </Panel>
          ))}
        </div>
      ) : null}
    </div>
  )
}
