import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicMafia, submitMafiaAction, submitMafiaVote, type MafiaPublicState } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { translate, type Lang } from '../i18n'

function useCountdown(deadlineTs: number | null): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!deadlineTs) return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [deadlineTs])
  if (!deadlineTs) return 0
  return Math.max(0, deadlineTs - Math.floor(now / 1000))
}

export function PublicMafiaActionPage() {
  const { token } = useParams<{ token: string }>()
  const [pageLang, setPageLang] = useState<Lang>('ru')
  const t = (key: string, params?: Record<string, string | number>) => translate(pageLang, key, params)
  const [state, setState] = useState<MafiaPublicState | null>(null)
  const [error, setError] = useState('')
  const [target, setTarget] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const roleLabel = (role: string) => t(`publicMafia.role.${role}`)
  const phaseLabel = (phase: string) => t(`publicMafia.phase.${phase}`)

  useEffect(() => {
    if (!token) return
    const load = () => {
      fetchPublicMafia(token)
        .then((s) => {
          setState(s)
          setError('')
          if (s.language === 'en' || s.language === 'ru') setPageLang(s.language)
        })
        .catch(() => setError(t('publicMafia.errorInvalid')))
    }
    load()
    const timer = setInterval(load, 4000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- poll by token; error text uses pageLang
  }, [token, pageLang])

  const remaining = useCountdown(state?.phase_deadline_ts ?? null)

  const targetOptions = useMemo(() => {
    if (!state) return []
    const options = state.alive_players.map((p) => ({ id: p.user_id, name: p.display_name }))
    return [{ id: '', name: t('game.skip') }, ...options]
  }, [state, pageLang])

  const isVotePhase = state?.phase === 'day_vote'

  const submit = async () => {
    if (!token) return
    setBusy(true)
    setMessage('')
    try {
      if (isVotePhase) {
        await submitMafiaVote(token, target || null)
      } else {
        await submitMafiaAction(token, target || null)
      }
      setMessage(t('game.sent'))
      const refreshed = await fetchPublicMafia(token)
      setState(refreshed)
    } catch {
      setMessage(t('game.sendFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (error) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-danger">{error}</p>
      </div>
    )
  }

  if (!state) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-muted">{t('common.loading')}</p>
      </div>
    )
  }

  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  const aliveCount = state.roster.filter((p) => p.alive).length

  return (
    <div className="flex min-h-dvh flex-col items-center bg-background p-6">
      <div className="flex w-full max-w-lg flex-col gap-4">
        <h1 className="text-lg font-semibold text-foreground">{t('publicMafia.title')}</h1>

        <Card className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">
              {t('game.round', { round: state.round_number })} · {phaseLabel(state.phase) ?? state.phase}
            </p>
            {state.game_status === 'active' && state.phase_deadline_ts && (
              <span className="text-xs font-medium text-muted">
                {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
              </span>
            )}
          </div>
          <p className="text-xl font-semibold text-foreground">
            {state.your_role ? roleLabel(state.your_role) : t('common.none')}
          </p>
          <p className="text-sm text-muted">
            {state.your_role ? t(`publicMafia.roleHint.${state.your_role}`) : ''}
          </p>
          {!state.your_alive && <p className="text-sm text-danger">{t('game.eliminated')}</p>}
          {state.game_status !== 'active' && (
            <p className="text-sm text-muted">
              {state.game_status === 'finished' ? t('game.finished') : t('game.cancelled')}
            </p>
          )}
        </Card>

        {state.your_role === 'mafia' && state.phase === 'night' && state.teammates && (
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-foreground">{t('publicMafia.mafiaTeam')}</h2>
            {state.teammates.length === 0 ? (
              <p className="text-sm text-muted">{t('publicMafia.mafiaTeamSolo')}</p>
            ) : (
              <ul className="flex flex-col gap-0.5 text-sm text-foreground">
                {state.teammates.map((m) => (
                  <li key={m.user_id}>{m.display_name}</li>
                ))}
              </ul>
            )}
          </Card>
        )}

        {state.action_required && (
          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">
                {isVotePhase ? t('publicMafia.dayVote') : t('publicMafia.nightAction')}
              </h2>
              <span className="text-sm text-muted">
                {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
              </span>
            </div>
            <Select
              value={target}
              onChange={setTarget}
              options={targetOptions}
              placeholder={isVotePhase ? t('publicMafia.executeWho') : t('publicMafia.selectTarget')}
            />
            <Button variant="primary" onClick={submit} disabled={busy}>
              {busy ? t('game.sending') : state.your_action_submitted ? t('game.changeChoice') : t('game.submit')}
            </Button>
            {state.your_action_submitted && (
              <p className="text-xs text-muted">
                {t('publicMafia.choiceSent', {
                  phase: isVotePhase ? t('publicMafia.votePhase') : t('publicMafia.nightPhase'),
                })}
              </p>
            )}
            {message && <p className="text-sm text-primary">{message}</p>}
          </Card>
        )}

        {isVotePhase && state.vote_tally && state.vote_tally.length > 0 && (
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-foreground">{t('game.currentVotes')}</h2>
            <ul className="flex flex-col gap-0.5 text-sm text-foreground">
              {state.vote_tally.map((entry) => (
                <li key={entry.target ?? 'skip'}>
                  {entry.target_display ?? t('game.skip')}: {entry.count}
                </li>
              ))}
            </ul>
          </Card>
        )}

        <Card className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-foreground">
            {t('game.players', { alive: aliveCount, total: state.roster.length })}
          </h2>
          <ul className="flex flex-col gap-0.5 text-sm">
            {state.roster.map((p) => (
              <li key={p.user_id} className={p.alive ? 'text-foreground' : 'text-muted line-through'}>
                {p.display_name}
                {p.role && ` — ${roleLabel(p.role)}`}
                {!p.alive && ' 💀'}
              </li>
            ))}
          </ul>
        </Card>

        {!state.action_required && state.your_alive && state.game_status === 'active' && (
          <p className="text-sm text-muted">
            {state.phase === 'night' ? t('publicMafia.waitNight') : t('publicMafia.waitDiscussion')}
          </p>
        )}
      </div>
    </div>
  )
}
