import { useEffect, useState } from 'react'
import { lookupFetch, type PluginEntry } from '../api/client'
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
    <div className="space-y-6">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold">{t('plugins.title')}</h1>
        <p className="mt-2 text-muted">{t('plugins.lead')}</p>
      </header>

      {plugins == null ? <p className="text-muted">{t('common.loading')}</p> : null}

      {plugins && plugins.length === 0 ? (
        <p className="rounded-[14px] border border-border bg-surface/70 p-5 text-sm text-muted">{t('plugins.empty')}</p>
      ) : null}

      {plugins && plugins.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {plugins.map((plugin) => (
            <article key={plugin.id} className="rounded-[14px] border border-border bg-surface/80 p-5">
              <h2 className="font-semibold">{plugin.name}</h2>
              <p className="mt-2 text-sm text-muted">
                {lang === 'ru' && plugin.description_ru ? plugin.description_ru : plugin.description}
              </p>
              <a
                href={plugin.url}
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex text-sm text-primary-hover hover:underline"
              >
                {t('plugins.open')}
              </a>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  )
}
