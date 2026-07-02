import { Card } from '../components/ui/Card'
import { useAuth } from '../context/AuthContext'

export function HomePage() {
  const { user } = useAuth()
  return (
    <Card className="animate-fade-in-up max-w-2xl">
      <h1 className="text-lg font-semibold text-foreground">Добро пожаловать, {user?.username}</h1>
      <p className="mt-2 text-sm text-muted">
        Выберите раздел слева. «Участники и роли» и «Lockdown и модерация» уже работают —
        остальные разделы появятся в следующих фазах.
      </p>
    </Card>
  )
}
