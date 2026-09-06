import { BADGE_CATALOG, type BadgeGroup } from '../lib/badges'
import { PageHeader, Panel } from '../components/ui'
import { useLanguage, useT } from '../context/LanguageContext'

const GROUPS: { id: BadgeGroup; titleKey: string; dense?: boolean }[] = [
  { id: 'general', titleKey: 'badges.group.general' },
  { id: 'bots', titleKey: 'badges.group.bots' },
  { id: 'gifting', titleKey: 'badges.group.gifting' },
  { id: 'accountAge', titleKey: 'badges.group.accountAge' },
  { id: 'streaming', titleKey: 'badges.group.streaming' },
  { id: 'gameTime', titleKey: 'badges.group.gameTime' },
  { id: 'gameVariety', titleKey: 'badges.group.gameVariety' },
  { id: 'nitro', titleKey: 'badges.group.nitro' },
  { id: 'nitroLegacy', titleKey: 'badges.group.nitroLegacy' },
  { id: 'boost', titleKey: 'badges.group.boost' },
  { id: 'server', titleKey: 'badges.group.server' },
  { id: 'special', titleKey: 'badges.group.special' },
  { id: 'tags', titleKey: 'badges.group.tags', dense: true },
  { id: 'fame', titleKey: 'badges.group.fame' },
  { id: 'legacy', titleKey: 'badges.group.legacy' },
  { id: 'other', titleKey: 'badges.group.other' },
]

export function BadgesPage() {
  const t = useT()
  const { lang } = useLanguage()

  return (
    <div className="space-y-10 lookup-rise">
      <PageHeader title={t('badges.title')} lead={t('badges.lead')} />
      <p className="text-xs leading-relaxed text-muted">
        {t('badges.attribution')}{' '}
        <a
          href="https://github.com/mezotv/discord-badges"
          target="_blank"
          rel="noreferrer"
          className="font-medium text-primary-hover hover:underline"
        >
          mezotv/discord-badges
        </a>{' '}
        (MIT).
      </p>

      {GROUPS.map((group) => {
        const items = BADGE_CATALOG.filter((b) => b.group === group.id)
        if (items.length === 0) return null
        return (
          <section key={group.id} className="space-y-4">
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="font-display text-lg font-semibold tracking-tight text-foreground sm:text-xl">
                {t(group.titleKey)}
              </h2>
              <span className="text-xs text-muted">{items.length}</span>
            </div>
            <div
              className={
                group.dense
                  ? 'grid grid-cols-3 gap-2.5 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8'
                  : 'grid gap-3 sm:grid-cols-2 lg:grid-cols-3'
              }
            >
              {items.map((badge) => {
                const name = lang === 'ru' ? badge.nameRu : badge.nameEn
                const desc =
                  lang === 'ru' ? badge.descriptionRu || badge.descriptionEn : badge.descriptionEn
                if (group.dense) {
                  return (
                    <Panel
                      key={badge.key}
                      className="lookup-card-lift group flex flex-col items-center gap-2 p-3 text-center transition-colors hover:border-primary/35"
                    >
                      <img
                        src={badge.icon}
                        alt=""
                        width={36}
                        height={36}
                        className="h-9 w-9 object-contain transition-transform duration-200 group-hover:scale-105"
                        loading="lazy"
                        onError={(e) => {
                          ;(e.currentTarget as HTMLImageElement).style.opacity = '0.25'
                        }}
                      />
                      <p className="line-clamp-2 text-[0.7rem] font-medium leading-snug text-foreground">{name}</p>
                    </Panel>
                  )
                }
                return (
                  <Panel
                    key={badge.key}
                    className="lookup-card-lift group flex gap-4 p-4 transition-colors hover:border-primary/35 sm:p-5"
                  >
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[12px] bg-primary-muted ring-1 ring-border/80 transition-transform duration-200 group-hover:scale-[1.04]">
                      <img
                        src={badge.icon}
                        alt=""
                        width={28}
                        height={28}
                        className="h-7 w-7 object-contain"
                        loading="lazy"
                        onError={(e) => {
                          ;(e.currentTarget as HTMLImageElement).style.opacity = '0.25'
                        }}
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
