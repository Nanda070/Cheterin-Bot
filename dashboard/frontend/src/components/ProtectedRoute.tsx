import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({
  children,
  requireGuild = true,
}: {
  children: ReactNode
  requireGuild?: boolean
}) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center text-slate-400">Загрузка...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Залогинен, но сервер ещё не выбран — на страницу выбора сервера.
  if (requireGuild && user.active_guild_id == null) {
    return <Navigate to="/servers" replace />
  }

  return <>{children}</>
}
