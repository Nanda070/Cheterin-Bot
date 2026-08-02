import { Compass } from '@phosphor-icons/react'
import { Link } from 'react-router-dom'
import { SecretClickTarget } from '../components/SecretClickTarget'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'
import { SECRET_ROOMS } from '../utils/easterEggs'

export function NotFoundPage() {
  const t = useT()

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 px-4">
      <Card className="animate-fade-in-up flex w-full max-w-sm flex-col items-center gap-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-muted">
          <Compass size={28} weight="fill" className="text-primary" />
        </div>

        <div className="flex flex-col gap-2">
          <SecretClickTarget clicks={10} to={SECRET_ROOMS.core} className="cursor-default">
            <h1 className="text-xl font-semibold text-foreground">{t('notFound.title')}</h1>
          </SecretClickTarget>
          <p className="text-sm text-muted">{t('notFound.body')}</p>
        </div>

        <Link
          to="/"
          className="text-sm font-medium text-primary transition-colors duration-200 ease-out hover:text-primary-hover"
        >
          {t('notFound.back')}
        </Link>
      </Card>
    </div>
  )
}
