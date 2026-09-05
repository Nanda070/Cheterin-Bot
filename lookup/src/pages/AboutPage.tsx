import { Link } from 'react-router-dom'
import { useT } from '../context/LanguageContext'

const ROOT = {
  about: '/about',
  docs: '/docs',
  panel: '/',
  terms: '/terms',
  privacy: '/privacy',
  cookies: '/cookies',
  disclaimer: '/disclaimer',
} as const

const PILLARS = ['product', 'independence', 'api'] as const
const SCOPE = ['user', 'bot', 'server', 'tools'] as const
const BOUNDARIES = ['b1', 'b2', 'b3', 'b4'] as const
type Bridge =
  | { key: 'bot' | 'docs' | 'panel'; href: string }
  | { key: 'lookup'; to: string }

const BRIDGES: Bridge[] = [
  { key: 'bot', href: ROOT.about },
  { key: 'docs', href: ROOT.docs },
  { key: 'panel', href: ROOT.panel },
  { key: 'lookup', to: '/' },
]

function BridgeCard({
  title,
  body,
  className,
}: {
  title: string
  body: string
  className: string
}) {
  return (
    <>
      <p className={`font-display text-base font-semibold transition-colors ${className}`}>{title}</p>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{body}</p>
      <span className="mt-4 text-xs font-semibold uppercase tracking-[0.14em] text-muted group-hover:text-primary-hover">
        →
      </span>
    </>
  )
}

export function AboutPage() {
  const t = useT()
  const cardClass = 'lookup-panel lookup-card-lift group flex flex-col p-5'

  return (
    <div>
      <section className="lookup-hero-in border-b border-border/70 pb-14 sm:pb-16">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-primary-hover">
          {t('about.eyebrow')}
        </p>
        <h1 className="mt-4 max-w-3xl font-display text-[2.05rem] font-bold leading-[1.1] tracking-tight sm:text-5xl md:text-[3.1rem]">
          {t('about.title')}
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-relaxed text-muted sm:text-lg">{t('about.lead')}</p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            to="/"
            className="inline-flex cursor-pointer rounded-[12px] bg-primary px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            {t('about.cta')}
          </Link>
          <a
            href={ROOT.about}
            className="inline-flex cursor-pointer rounded-[12px] border border-border bg-surface px-5 py-3 text-sm font-semibold text-foreground transition-colors hover:border-primary/40 hover:bg-surface-hover"
          >
            {t('about.ctaBot')}
          </a>
        </div>
      </section>

      <section className="lookup-rise lookup-rise-delay-1">
        {PILLARS.map((key, index) => (
          <article
            key={key}
            className="grid gap-4 border-b border-border/70 py-10 sm:gap-8 sm:py-12 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.15fr)] lg:gap-14"
          >
            <div>
              <p className="font-display text-xs font-semibold tracking-[0.2em] text-primary/85">
                {String(index + 1).padStart(2, '0')}
              </p>
              <h2 className="mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">
                {t(`about.pillar.${key}.title`)}
              </h2>
            </div>
            <p className="max-w-xl text-base leading-relaxed text-muted">{t(`about.pillar.${key}.body`)}</p>
          </article>
        ))}
      </section>

      <section className="lookup-rise lookup-rise-delay-2 border-b border-border/70 py-14 sm:py-16">
        <div className="max-w-2xl">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-primary-hover">
            {t('about.scope.eyebrow')}
          </p>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {t('about.scope.title')}
          </h2>
          <p className="mt-3 text-base leading-relaxed text-muted">{t('about.scope.lead')}</p>
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {SCOPE.map((key) => (
            <article key={key} className="lookup-panel lookup-card-lift p-5">
              <h3 className="font-display text-base font-semibold">{t(`about.scope.${key}.title`)}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{t(`about.scope.${key}.body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="lookup-rise lookup-rise-delay-3 border-b border-border/70 py-14 sm:py-16">
        <div className="max-w-2xl">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-primary-hover">
            {t('about.bounds.eyebrow')}
          </p>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {t('about.bounds.title')}
          </h2>
          <p className="mt-3 text-base leading-relaxed text-muted">{t('about.bounds.lead')}</p>
        </div>
        <ul className="mt-8 grid gap-3 sm:grid-cols-2">
          {BOUNDARIES.map((key) => (
            <li key={key} className="lookup-panel flex gap-3 p-5">
              <span className="mt-2 h-px w-4 shrink-0 bg-primary" aria-hidden />
              <p className="text-sm leading-relaxed text-foreground/90">{t(`about.bounds.${key}`)}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="lookup-rise border-b border-border/70 py-14 sm:py-16">
        <div className="max-w-2xl">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-primary-hover">
            {t('about.bridge.eyebrow')}
          </p>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
            {t('about.bridge.title')}
          </h2>
          <p className="mt-3 text-base leading-relaxed text-muted">{t('about.bridge.lead')}</p>
        </div>
        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {BRIDGES.map((item) => {
            const title = t(`about.bridge.${item.key}.title`)
            const body = t(`about.bridge.${item.key}.body`)
            if ('href' in item) {
              return (
                <a key={item.key} href={item.href} className={cardClass}>
                  <BridgeCard title={title} body={body} className="group-hover:text-primary-hover" />
                </a>
              )
            }
            return (
              <Link key={item.key} to={item.to} className={cardClass}>
                <BridgeCard title={title} body={body} className="group-hover:text-primary-hover" />
              </Link>
            )
          })}
        </div>
      </section>

      <section className="lookup-rise py-14 sm:py-16">
        <div className="lookup-panel-raised relative overflow-hidden p-6 sm:p-8 md:p-10">
          <div
            className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-primary/10 blur-3xl"
            aria-hidden
          />
          <div className="relative grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:items-end">
            <div>
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-primary-hover">
                {t('about.legal.eyebrow')}
              </p>
              <h2 className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
                {t('about.legal.title')}
              </h2>
              <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{t('about.legal.body')}</p>
              <ul className="mt-5 flex flex-wrap gap-x-4 gap-y-2 text-sm">
                <li>
                  <a href={ROOT.terms} className="text-foreground/90 underline-offset-4 hover:underline">
                    {t('footer.terms')}
                  </a>
                </li>
                <li>
                  <a href={ROOT.privacy} className="text-foreground/90 underline-offset-4 hover:underline">
                    {t('footer.privacy')}
                  </a>
                </li>
                <li>
                  <a href={ROOT.cookies} className="text-foreground/90 underline-offset-4 hover:underline">
                    {t('footer.cookies')}
                  </a>
                </li>
                <li>
                  <a href={ROOT.disclaimer} className="text-foreground/90 underline-offset-4 hover:underline">
                    {t('footer.disclaimer')}
                  </a>
                </li>
              </ul>
            </div>
            <div className="flex flex-wrap gap-3 lg:justify-end">
              <Link
                to="/"
                className="inline-flex cursor-pointer rounded-[12px] bg-primary px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
              >
                {t('about.cta')}
              </Link>
              <a
                href={ROOT.docs}
                className="inline-flex cursor-pointer rounded-[12px] border border-border bg-surface px-5 py-3 text-sm font-semibold text-foreground transition-colors hover:border-primary/40 hover:bg-surface-hover"
              >
                {t('about.ctaDocs')}
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
