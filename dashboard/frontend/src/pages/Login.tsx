import { BookOpen, DiscordLogo, Headset, Package, ShieldCheck, Sparkle } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { loginUrl } from '../api/client'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

const FEATURE_KEYS = [
  { icon: ShieldCheck, key: 'login.feature.moderation' as const },
  { icon: Package, key: 'login.feature.supply' as const },
  { icon: Headset, key: 'login.feature.voice' as const },
]

export function LoginPage() {
  const t = useT()

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 px-4 py-10">
      <div className="flex items-center gap-2 text-foreground">
        <Sparkle size={24} weight="fill" className="text-primary" />
        <span className="text-lg font-semibold">Cheterin</span>
      </div>

      <Card className="animate-fade-in-up flex w-full max-w-sm flex-col items-center gap-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-muted">
          <ShieldCheck size={28} weight="fill" className="text-primary" />
        </div>

        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold text-foreground">{t('login.title')}</h1>
          <p className="text-sm text-muted">{t('login.subtitle')}</p>
        </div>

        <a
          href={loginUrl()}
          className={[
            'inline-flex w-full cursor-pointer items-center justify-center gap-2 rounded-control px-4 py-2.5',
            'bg-primary text-sm font-medium text-white transition-all duration-200 ease-out',
            'shadow-[0_0_0_1px_rgba(88,101,242,0.4),0_8px_20px_-6px_rgba(88,101,242,0.55)]',
            'hover:bg-primary-hover',
          ].join(' ')}
        >
          <DiscordLogo size={20} weight="fill" />
          {t('login.button')}
        </a>

        <ul className="flex w-full flex-col gap-2 text-left">
          {FEATURE_KEYS.map(({ icon: FeatureIcon, key }) => (
            <li key={key} className="flex items-center gap-2 text-xs text-muted">
              <FeatureIcon size={16} className="shrink-0 text-primary" />
              {t(key)}
            </li>
          ))}
        </ul>
      </Card>

      <div className="flex flex-col items-center gap-3">
        <p className="text-xs text-muted">{t('login.footer')}</p>
        <nav className="flex items-center gap-4 text-sm">
          <Link to="/docs" className="flex items-center gap-1 text-muted transition-colors hover:text-foreground">
            <BookOpen size={16} />
            {t('nav.docs')}
          </Link>
          <Link to="/terms" className="text-muted transition-colors hover:text-foreground">
            {t('nav.terms')}
          </Link>
          <Link to="/privacy" className="text-muted transition-colors hover:text-foreground">
            {t('nav.privacy')}
          </Link>
        </nav>
      </div>
    </div>
  )
}
