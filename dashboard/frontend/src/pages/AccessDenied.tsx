import { ShieldWarning } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { LanguageToggle } from '../components/LanguageToggle'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

export function AccessDeniedPage() {
  const t = useT()

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 px-4">
      <div className="flex w-full max-w-sm justify-end">
        <LanguageToggle />
      </div>
      <Card className="animate-fade-in-up flex w-full max-w-sm flex-col items-center gap-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-danger/10">
          <ShieldWarning size={28} weight="fill" className="text-danger" />
        </div>

        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold text-foreground">{t('accessDenied.title')}</h1>
          <p className="text-sm text-muted">{t('accessDenied.body')}</p>
        </div>

        <div className="flex flex-col items-center gap-2">
          <Link
            to="/login"
            className="text-sm font-medium text-primary transition-colors duration-200 ease-out hover:text-primary-hover"
          >
            {t('accessDenied.back')}
          </Link>
          <Link to="/servers" className="text-sm text-muted transition-colors hover:text-foreground">
            {t('nav.switchServer')}
          </Link>
        </div>
      </Card>
    </div>
  )
}
