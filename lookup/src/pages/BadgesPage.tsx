import { BADGE_CATALOG, type BadgeDef } from '../lib/badges'
import { PageHeader, Panel } from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'

const GROUPS: { id: BadgeDef['group']; titleKey: string }[] = [
  { id: 'flags', titleKey: 'badges.group.flags' },
  { id: 'nitro', titleKey: 'badges.group.nitro' },
  { id: 'boost', titleKey: 'badges.group.boost' },
]

export function BadgesPage() {
  const t = useT()
  const { lang } = useLanguage()

  return (
    <div className="space-y-10 lookup-rise">
      <PageHeader title={t('badges.title')} lead={t('badges.lead')} />

      {GROUPS.map((group) => {
        const items = BADGE_CATALOG.filter((b) => b.group === group.id)
        if (items.length === 0) return null
        return (
          <section key={group.id} className="space-y-4">
            <h2 className="font-display text-lg font-semibold tracking-tight text-foreground sm:text-xl">
              {t(group.titleKey)}
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((badge) => {
                const name = lang === 'ru' ? badge.nameRu : badge.nameEn
                const desc =
                  lang === 'ru' ? badge.descriptionRu || badge.descriptionEn : badge.descriptionEn
                return (
                  <Panel
                    key={badge.key}
                    className="lookup-card-lift group flex gap-4 p-4 transition-colors focus-within:border-primary/40 hover:border-primary/35 sm:p-5"
                  >
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[12px] bg-primary-muted ring-1 ring-border/80 transition-transform duration-200 group-hover:scale-[1.04]">
                      <img
                        src={badge.icon}
                        alt=""
                        width={28}
                        height={28}
                        className="h-7 w-7 object-contain"
                        loading="lazy"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-display text-sm font-semibold leading-snug text-foreground sm:text-base">
                        {name}
                      </h3>
                      {desc ? (
                        <p className="mt-1.5 text-xs leading-relaxed text-muted sm:text-sm">{desc}</p>
                      ) : null}
                      {badge.bit !== 0 ? (
                        <p className="mt-2 font-mono text-[0.7rem] text-muted/90">
                          {t('badges.bit')}: {badge.bit} (1 &lt;&lt; {Math.log2(badge.bit)})
                        </p>
                      ) : (
                        <p className="mt-2 text-[0.7rem] uppercase tracking-[0.12em] text-muted/80">
                          {t('badges.catalogOnly')}
                        </p>
                      )}
                    </div>
                  </Panel>
                )
              })}
            </div>
          </section>
        )
      })}
    </div>
  )
}
