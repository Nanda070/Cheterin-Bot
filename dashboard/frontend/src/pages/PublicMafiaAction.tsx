import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { fetchPublicMafia, submitMafiaAction, submitMafiaVote, type MafiaPublicState } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'

const ROLE_LABEL: Record<string, string> = {
  mafia: 'Мафия',
  citizen: 'Мирный житель',
  doctor: 'Доктор',
  sheriff: 'Шериф',
}

const ROLE_HINT: Record<string, string> = {
  mafia: 'Ночью вместе с командой выбираете, кого убить. Решает большинство голосов команды.',
  doctor: 'Ночью можете вылечить одного игрока (в том числе себя), защитив его от убийства.',
  sheriff: 'Ночью можете проверить одного игрока — узнаете, состоит ли он в мафии.',
  citizen: 'У вас нет ночных действий — участвуйте в дневном голосовании за казнь прямо на этой странице.',
}

const PHASE_LABEL: Record<string, string> = {
  lobby: 'Лобби',
  night: 'Ночь',
  day_discussion: 'Обсуждение',
  day_vote: 'Голосование',
  ended: 'Игра завершена',
}

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
  const [state, setState] = useState<MafiaPublicState | null>(null)
  const [error, setError] = useState('')
  const [target, setTarget] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) return
    const load = () => {
      fetchPublicMafia(token)
        .then((s) => {
          setState(s)
          setError('')
        })
        .catch(() => setError('Ссылка недействительна или игра не найдена.'))
    }
    load()
    const timer = setInterval(load, 4000)
    return () => clearInterval(timer)
  }, [token])

  const remaining = useCountdown(state?.phase_deadline_ts ?? null)

  const targetOptions = useMemo(() => {
    if (!state) return []
    const options = state.alive_players.map((p) => ({ id: p.user_id, name: p.display_name }))
    return [{ id: '', name: 'Пропустить' }, ...options]
  }, [state])

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
      setMessage('Отправлено.')
      const refreshed = await fetchPublicMafia(token)
      setState(refreshed)
    } catch {
      setMessage('Не удалось отправить.')
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
        <p className="text-sm text-muted">Загрузка…</p>
      </div>
    )
  }

  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  const aliveCount = state.roster.filter((p) => p.alive).length

  return (
    <div className="flex min-h-dvh flex-col items-center bg-background p-6">
      <div className="flex w-full max-w-lg flex-col gap-4">
        <h1 className="text-lg font-semibold text-foreground">Игра «Мафия»</h1>

        <Card className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted">
              Раунд {state.round_number} · {PHASE_LABEL[state.phase] ?? state.phase}
            </p>
            {state.game_status === 'active' && state.phase_deadline_ts && (
              <span className="text-xs font-medium text-muted">
                {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
              </span>
            )}
          </div>
          <p className="text-xl font-semibold text-foreground">
            {state.your_role ? ROLE_LABEL[state.your_role] : '—'}
          </p>
          <p className="text-sm text-muted">{state.your_role ? ROLE_HINT[state.your_role] : ''}</p>
          {!state.your_alive && <p className="text-sm text-danger">Ты выбыл из игры.</p>}
          {state.game_status !== 'active' && (
            <p className="text-sm text-muted">
              {state.game_status === 'finished' ? 'Игра завершена.' : 'Игра отменена.'}
            </p>
          )}
        </Card>

        {state.your_role === 'mafia' && state.phase === 'night' && state.teammates && (
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-foreground">Команда мафии</h2>
            {state.teammates.length === 0 ? (
              <p className="text-sm text-muted">Ты единственный представитель мафии.</p>
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
              <h2 className="text-sm font-semibold text-foreground">{isVotePhase ? 'Дневное голосование' : 'Ночное действие'}</h2>
              <span className="text-sm text-muted">
                {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
              </span>
            </div>
            <Select
              value={target}
              onChange={setTarget}
              options={targetOptions}
              placeholder={isVotePhase ? 'Кого казнить?' : 'Выберите цель…'}
            />
            <Button variant="primary" onClick={submit} disabled={busy}>
              {busy ? 'Отправляем…' : state.your_action_submitted ? 'Изменить выбор' : 'Отправить'}
            </Button>
            {state.your_action_submitted && (
              <p className="text-xs text-muted">
                Выбор уже отправлен — можно изменить до конца {isVotePhase ? 'голосования' : 'ночи'}.
              </p>
            )}
            {message && <p className="text-sm text-primary">{message}</p>}
          </Card>
        )}

        {isVotePhase && state.vote_tally && state.vote_tally.length > 0 && (
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-foreground">Текущие голоса</h2>
            <ul className="flex flex-col gap-0.5 text-sm text-foreground">
              {state.vote_tally.map((entry) => (
                <li key={entry.target ?? 'skip'}>
                  {entry.target_display ?? 'Пропустить'}: {entry.count}
                </li>
              ))}
            </ul>
          </Card>
        )}

        <Card className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-foreground">
            Игроки ({aliveCount}/{state.roster.length})
          </h2>
          <ul className="flex flex-col gap-0.5 text-sm">
            {state.roster.map((p) => (
              <li key={p.user_id} className={p.alive ? 'text-foreground' : 'text-muted line-through'}>
                {p.display_name}
                {p.role && ` — ${ROLE_LABEL[p.role]}`}
                {!p.alive && ' 💀'}
              </li>
            ))}
          </ul>
        </Card>

        {!state.action_required && state.your_alive && state.game_status === 'active' && (
          <p className="text-sm text-muted">
            {state.phase === 'night' ? 'Сейчас не твой ход — жди утра.' : 'Сейчас обсуждение — скоро начнётся голосование.'}
          </p>
        )}
      </div>
    </div>
  )
}
