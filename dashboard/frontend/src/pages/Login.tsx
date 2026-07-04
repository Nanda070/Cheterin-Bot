import { DiscordLogo, ShieldCheck } from '@phosphor-icons/react'
import { loginUrl } from '../api/client'
import { Card } from '../components/ui/Card'

export function LoginPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 px-4">
      <Card className="animate-fade-in-up flex w-full max-w-sm flex-col items-center gap-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-muted">
          <ShieldCheck size={28} weight="fill" className="text-primary" />
        </div>

        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold text-foreground">Cheterin</h1>
          <p className="text-sm text-muted">
            Войдите через Discord, чтобы получить доступ к панели модерации сервера.
          </p>
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
          Войти через Discord
        </a>
      </Card>

      <p className="text-xs text-muted">Доступ только для модераторов и администраторов сервера</p>
    </div>
  )
}
