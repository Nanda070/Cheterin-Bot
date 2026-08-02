import {
  Crosshair,
  Detective,
  FirstAidKit,
  Knife,
  Moon,
  SpeakerSimpleHigh,
  SpeakerSimpleSlash,
  Skull,
  Sun,
  Timer,
  UsersThree,
} from '@phosphor-icons/react'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicMafia, submitMafiaAction, submitMafiaVote, type MafiaPublicState, type MafiaRole } from '../api/client'
import { GameAvatar } from '../components/GameAvatar'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { useActionRequiredAlert } from '../hooks/useActionRequiredAlert'
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

function formatTimer(remaining: number): string {
  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

const ROLE_ICON: Record<MafiaRole, ReactNode> = {
  mafia: <Knife size={22} weight="fill" />,
  doctor: <FirstAidKit size={22} weight="fill" />,
  sheriff: <Detective size={22} weight="fill" />,
  citizen: <UsersThree size={22} weight="fill" />,
}

export function PublicMafiaActionPage() {
  const { token } = useParams<{ token: string }>()
  const [pageLang, setPageLang] = useState<Lang>(() =>
    typeof navigator !== 'undefined' && navigator.language.toLowerCase().startsWith('en') ? 'en' : 'ru',
  )
  const t = (key: string, params?: Record<string, string | number>) => translate(pageLang, key, params)
  const [state, setState] = useState<MafiaPublicState | null>(null)
  const [error, setError] = useState('')
  const [target, setTarget] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const roleLabel = (role: string) => t(`publicMafia.role.${role}`)
  // API phases are snake_case (`day_vote`); keys must match (not camelCase like mafia.phase.dayVote).
  const phaseLabel = (phase: string) => {
    const key = `publicMafia.phase.${phase}`
    const label = t(key)
    return label === key ? phase : label
  }

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
  const timerUrgent = remaining > 0 && remaining <= 30
  const { muted, toggleMuted } = useActionRequiredAlert(state?.action_required ?? false, t('game.titleFlashYourTurn'))

  const targetOptions = useMemo(() => {
    if (!state) return []
    const options = state.alive_players.map((p) => ({ id: p.user_id, name: p.display_name }))
    return [{ id: '', name: t('game.skip') }, ...options]
  }, [state, pageLang])

  const isVotePhase = state?.phase === 'day_vote'
  const isNight = state?.phase === 'night'

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
      <div className="game-table game-table--mafia flex min-h-dvh items-center justify-center p-6">
        <p className="text-sm text-danger">{error}</p>
      </div>
    )
  }

  if (!state) {
    return (
      <div className="game-table game-table--mafia flex min-h-dvh items-center justify-center p-6">
        <p className="text-sm text-muted">{t('common.loading')}</p>
      </div>
    )
  }

  const aliveCount = state.roster.filter((p) => p.alive).length
  const timerText = formatTimer(remaining)
  const role = state.your_role
  const tableTone = isNight ? 'game-table--night' : 'game-table--day'

  return (
    <div className={`game-table game-table--mafia ${tableTone} min-h-dvh`}>
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6">
        <header className="game-hud animate-fade-in-up sticky top-3 z-10 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-card)] border border-border/70 px-4 py-3 backdrop-blur-md">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">{t('publicMafia.title')}</p>
            <h1 className="flex items-center gap-2 truncate text-lg font-semibold text-foreground sm:text-xl">
              {isNight ? <Moon size={20} weight="fill" className="text-primary" /> : <Sun size={20} weight="fill" className="text-warning" />}
              {t('game.round', { round: state.round_number })} · {phaseLabel(state.phase)}
            </h1>
          </div>
          <div className="flex items-center gap-2">
            {state.game_status === 'active' && state.phase_deadline_ts && (
              <div
                className={`game-timer flex items-center gap-2 rounded-control px-3 py-2 ${
                  timerUrgent ? 'game-timer--urgent' : ''
                }`}
              >
                <Timer size={18} weight="bold" className={timerUrgent ? 'text-danger' : 'text-primary'} />
                <span className={`font-mono text-lg font-semibold tabular-nums ${timerUrgent ? 'text-danger' : 'text-foreground'}`}>
                  {timerText}
                </span>
              </div>
            )}
            <button
              type="button"
              onClick={toggleMuted}
              title={muted ? t('game.unmuteAlerts') : t('game.muteAlerts')}
              aria-label={muted ? t('game.unmuteAlerts') : t('game.muteAlerts')}
              className="game-timer flex items-center justify-center rounded-control p-2.5 text-muted transition-colors hover:text-foreground"
            >
              {muted ? <SpeakerSimpleSlash size={18} weight="bold" /> : <SpeakerSimpleHigh size={18} weight="bold" />}
            </button>
          </div>
        </header>

        <section className="game-panel game-role-card animate-fade-in-up flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/70 p-5" style={{ animationDelay: '60ms' }}>
          <div className="flex items-start gap-4">
            <div className="game-role-icon flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-primary">
              {role ? ROLE_ICON[role] : <UsersThree size={22} weight="fill" />}
            </div>
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-wide text-muted">{t('publicMafia.title')}</p>
              <p className="text-2xl font-semibold text-foreground">
                {role ? roleLabel(role) : t('common.none')}
              </p>
              <p className="mt-1 text-sm text-muted">
                {role ? t(`publicMafia.roleHint.${role}`) : ''}
              </p>
            </div>
          </div>
          {!state.your_alive && (
            <p className="flex items-center gap-2 text-sm text-danger">
              <Skull size={16} weight="fill" />
              {t('game.eliminated')}
            </p>
          )}
          {state.game_status !== 'active' && (
            <p className="text-sm text-muted">
              {state.game_status === 'finished' ? t('game.finished') : t('game.cancelled')}
            </p>
          )}
        </section>

        {state.your_role === 'mafia' && state.phase === 'night' && state.teammates && (
          <section className="game-panel animate-fade-in-up flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/70 p-4" style={{ animationDelay: '100ms' }}>
            <div className="flex items-center gap-2">
              <Knife size={18} weight="fill" className="text-primary" />
              <h2 className="text-sm font-semibold text-foreground">{t('publicMafia.mafiaTeam')}</h2>
            </div>
            {state.teammates.length === 0 ? (
              <p className="text-sm text-muted">{t('publicMafia.mafiaTeamSolo')}</p>
            ) : (
              <ul className="grid gap-2 sm:grid-cols-2">
                {state.teammates.map((m) => (
                  <li key={m.user_id} className="flex items-center gap-2.5 rounded-control border border-border/70 bg-background/35 px-3 py-2">
                    <GameAvatar name={m.display_name} avatarUrl={m.avatar_url} size="sm" />
                    <span className="truncate text-sm text-foreground">{m.display_name}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        {state.action_required && (
          <section className="game-panel game-panel--action flex flex-col gap-3 rounded-[var(--radius-card)] border border-primary/40 p-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <Crosshair size={16} weight="bold" className="text-primary" />
                {isVotePhase ? t('publicMafia.dayVote') : t('publicMafia.nightAction')}
              </h2>
              <span className={`font-mono text-sm tabular-nums ${timerUrgent ? 'text-danger' : 'text-muted'}`}>
                {timerText}
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
          </section>
        )}

        {isVotePhase && state.vote_tally && state.vote_tally.length > 0 && (
          <section className="game-panel flex flex-col gap-2 rounded-[var(--radius-card)] border border-border/70 p-4">
            <h2 className="text-sm font-semibold text-foreground">{t('game.currentVotes')}</h2>
            <ul className="flex flex-col gap-1.5 text-sm text-foreground">
              {state.vote_tally.map((entry) => (
                <li key={entry.target ?? 'skip'} className="rounded-control bg-background/40 px-3 py-2 text-sm text-foreground">
                  {entry.target_display ?? t('game.skip')}: {entry.count}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="game-panel flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/70 p-4">
          <div className="flex items-center gap-2">
            <UsersThree size={18} weight="fill" className="text-primary" />
            <h2 className="text-sm font-semibold text-foreground">
              {t('game.players', { alive: aliveCount, total: state.roster.length })}
            </h2>
          </div>
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {state.roster.map((p) => (
              <li
                key={p.user_id}
                className={`flex flex-col items-center gap-2 rounded-control border px-3 py-3 text-center ${
                  p.alive ? 'border-border/70 bg-background/35' : 'border-border/40 bg-background/20'
                }`}
              >
                <GameAvatar name={p.display_name} avatarUrl={p.avatar_url} alive={p.alive} size="lg" />
                <div className="min-w-0 w-full">
                  <p className={`truncate text-sm font-medium ${p.alive ? 'text-foreground' : 'text-muted line-through'}`}>
                    {p.display_name}
                    {p.role && ` — ${roleLabel(p.role)}`}
                    {!p.alive && ' 💀'}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        {!state.action_required && state.your_alive && state.game_status === 'active' && (
          <p className="text-center text-sm text-muted">
            {state.phase === 'night' ? t('publicMafia.waitNight') : t('publicMafia.waitDiscussion')}
          </p>
        )}
      </div>
    </div>
  )
}
