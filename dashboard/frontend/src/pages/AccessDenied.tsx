import { ShieldWarning } from '@phosphor-icons/react'
import { Card } from '../components/ui/Card'

export function AccessDeniedPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-8 px-4">
      <Card className="animate-fade-in-up flex w-full max-w-sm flex-col items-center gap-4 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-danger/10">
          <ShieldWarning size={28} weight="fill" className="text-danger" />
        </div>

        <div className="flex flex-col gap-2">
          <h1 className="text-xl font-semibold text-foreground">Доступ запрещён</h1>
          <p className="text-sm text-muted">
            У вашей учётной записи нет прав для просмотра этой панели. Доступ есть только у
            модераторов и администраторов сервера.
          </p>
        </div>

        <a
          href="/login"
          className="text-sm font-medium text-primary transition-colors duration-200 ease-out hover:text-primary-hover"
        >
          Вернуться на страницу входа
        </a>
      </Card>
    </div>
  )
}
