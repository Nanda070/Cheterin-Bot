import { Navigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useT } from '../context/LanguageContext'
import { LandingPage } from './Landing'

const AUTH_ERROR_KEYS: Record<string, string> = {
  denied: 'login.error.denied',
  state_mismatch: 'login.error.stateMismatch',
  oauth_failed: 'login.error.oauthFailed',
}

export function LoginPage() {
  const t = useT()
  const { user, isLoading } = useAuth()
  const [params] = useSearchParams()
  const authError = params.get('auth_error')
  const errorKey = authError ? AUTH_ERROR_KEYS[authError] : undefined

  if (!isLoading && user) {
    return <Navigate to={user.active_guild_id ? '/' : '/servers'} replace />
  }

  if (authError === 'denied') {
    return <Navigate to="/access-denied" replace />
  }

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted">{t('common.loading')}</div>
    )
  }

  return <LandingPage authErrorKey={errorKey} />
}
