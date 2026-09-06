import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { lookupFetch, type PluginEntry } from '../api/client'
import { EmptyState, LoadingBlock, PageHeader, Panel } from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'

type SectionId = 'lookup' | 'vencord' | 'external'

const SECTIONS: { id: SectionId; titleKey: string; match: (p: PluginEntry) => boolean }[] = [
  {
    id: 'lookup',
    titleKey: 'plugins.section.lookup',
    match: (p) => (p.tags ?? []).includes('lookup'),
  },
  {
    id: 'vencord',
    titleKey: 'plugins.section.vencord',
    match: (p) => (p.tags ?? []).includes('vencord') || (p.tags ?? []).includes('userplugins'),
  },
  {
    id: 'external',
    titleKey: 'plugins.section.external',
    match: (p) => {
      const tags = p.tags ?? []
      return !tags.includes('lookup') && !tags.includes('vencord') && !tags.includes('userplugins')
    },
  },
]

function isInternal(url: string) {
  return url.startsWith('/lookup/') || url.startsWith('/')
}

function internalTo(url: string) {
  if (url.startsWith('/lookup/')) return url.slice('/lookup'.length) || '/'
  return url
}

export function PluginsPage() {
  const t = useT()
  const { lang } = useLanguage()
  const [plugins, setPlugins] = useState<PluginEntry[] | null>(null)

  useEffect(() => {
    void lookupFetch<{ plugins: PluginEntry[] }>('/plugins')
      .then((res) => setPlugins(res.plugins))
      .catch(() => setPlugins([]))
  }, [])

  const sections = useMemo(() => {
    if (!plugins) return []
    return SECTIONS.map((section) => ({
      ...section,
      items: plugins.filter(section.match),
    })).filter((s) => s.items.length > 0)
  }, [plugins])

  return (
    <div className="space-y-10 lookup-rise">
      <PageHeader title={t('plugins.title')} lead={t('plugins.lead')} />

      {plugins == null ? <LoadingBlock rows={3} /> : null}

      {plugins && plugins.length === 0 ? (
        <EmptyState title={t('plugins.title')} body={t('plugins.empty')} />
      ) : null}

      {sections.map((section) => (
        <section key={section.id} className="space-y-4">
          <h2 className="font-display text-lg font-semibold tracking-tight text-foreground sm:text-xl">
            {t(section.titleKey)}
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {section.items.map((plugin) => {
              const desc =
                lang === 'ru' && plugin.description_ru ? plugin.description_ru : plugin.description
              const tags = plugin.tags ?? []
              const card = (
                <Panel className="lookup-card-lift flex h-full flex-col p-5 sm:p-6">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-display text-lg font-semibold text-foreground">{plugin.name}</h3>
                    {tags.includes('userplugins') ? (
                      <span className="rounded-full border border-primary/35 bg-primary-muted px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-[0.1em] text-primary-hover">
                        UserPlugin
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{desc}</p>
                  <span className="mt-5 inline-flex text-sm font-semibold text-primary-hover">
                    {t('plugins.open')} →
                  </span>
                </Panel>
              )

              if (isInternal(plugin.url)) {
                return (
                  <Link key={plugin.id} to={internalTo(plugin.url)} className="block h-full">
                    {card}
                  </Link>
                )
              }

              return (
                <a
                  key={plugin.id}
                  href={plugin.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block h-full"
                >
                  {card}
                </a>
              )
            })}
          </div>
        </section>
      ))}
    </div>
  )
}
