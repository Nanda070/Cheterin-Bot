import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicBracket, type BracketDetail } from '../api/client'
import { BracketView } from '../components/BracketView'
import { useT } from '../context/LanguageContext'

export function PublicBracketPage() {
  const t = useT()
  const { token } = useParams<{ token: string }>()
  const [bracket, setBracket] = useState<BracketDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    fetchPublicBracket(token)
      .then(setBracket)
      .catch(() => setError(t('publicBracket.errorNotFound')))
  }, [token, t])

  if (error) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-danger">{error}</p>
      </div>
    )
  }

  if (!bracket) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-muted">{t('common.loading')}</p>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-background p-6">
      <h1 className="mb-6 text-lg font-semibold text-foreground">{bracket.title}</h1>
      <BracketView bracket={bracket} />
    </div>
  )
}
