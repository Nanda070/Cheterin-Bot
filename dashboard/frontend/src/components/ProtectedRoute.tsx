import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'

export function ProtectedRoute({
  children,
  requireGuild = true,
}: {
  children: ReactNode
  requireGuild?: boolean
}) {
  const { user, isLoading, accessDenied } = useAuth()
  const t = useT()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-muted">{t('common.loading')}</div>
    )
  }

  if (accessDenied) {
    return <Navigate to="/access-denied" replace />
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (requireGuild && user.active_guild_id == null) {
    return <Navigate to="/servers" replace />
  }

  return <>{children}</>
}
