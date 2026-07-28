import {
  Briefcase,
  Handbag,
  Heart,
  IdentificationCard,
  Lightning,
  Person,
  ShieldWarning,
  Skull,
  Timer,
  UsersThree,
  Warning,
} from '@phosphor-icons/react'
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useParams } from 'react-router-dom'
import {
  announceBunkerAbility,
  fetchPublicBunker,
  revealBunkerFields,
  submitBunkerVote,
  BUNKER_FIELD_KEYS,
  type BunkerCharacter,
  type BunkerFieldKey,
  type BunkerPublicState,
} from '../api/client'
import { GameAvatar } from '../components/GameAvatar'
import { Button } from '../components/ui/Button'
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

function formatTimer(remaining: number): string {
  const minutes = Math.floor(remaining / 60)
  const seconds = remaining % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

const FIELD_ICON: Record<BunkerFieldKey, ReactNode> = {
  profession: <Briefcase size={16} weight="fill" />,
  age: <IdentificationCard size={16} weight="fill" />,
  gender: <Person size={16} weight="fill" />,
  body_type: <Person size={16} weight="duotone" />,
  health: <Heart size={16} weight="fill" />,
  hobby: <Lightning size={16} weight="fill" />,
  phobia: <ShieldWarning size={16} weight="fill" />,
  backpack_item: <Handbag size={16} weight="fill" />,
  large_item: <Handbag size={16} weight="duotone" />,
  trait: <IdentificationCard size={16} weight="duotone" />,
  additional_info: <Warning size={16} weight="fill" />,
}

export function PublicBunkerActionPage() {
  const { token } = useParams<{ token: string }>()
  const [pageLang, setPageLang] = useState<Lang>('ru')
  const t = (key: string, params?: Record<string, string | number>) => translate(pageLang, key, params)
  const [state, setState] = useState<BunkerPublicState | null>(null)
  const [error, setError] = useState('')
  const [voteTarget, setVoteTarget] = useState('')
  const [voteBusy, setVoteBusy] = useState(false)
  const [voteMessage, setVoteMessage] = useState('')

  const [abilityCardIndex, setAbilityCardIndex] = useState<1 | 2 | null>(null)
  const [abilityTarget, setAbilityTarget] = useState('')
  const [abilityNote, setAbilityNote] = useState('')
  const [abilityBusy, setAbilityBusy] = useState(false)
  const [abilityMessage, setAbilityMessage] = useState('')

  const fieldLabel = (key: BunkerFieldKey) => t(`publicBunker.field.${key}`)
  const phaseLabel = (phase: string) => t(`publicBunker.phase.${phase}`)

  const fieldValue = (key: BunkerFieldKey, character: BunkerCharacter): string => {
    switch (key) {
      case 'profession':
        if (!character.profession) return t('common.none')
        return `${character.profession.name} (${character.profession.experience_level}${character.profession.has_ability ? t('bunker.abilityHasAbility') : ''}) — ${character.profession.category}`
      case 'age':
        return character.age?.label ?? t('common.none')
      case 'gender':
        return character.gender ?? t('common.none')
      case 'body_type':
        return character.body_type?.name ?? t('common.none')
      case 'health':
        if (!character.health) return t('common.none')
        return character.health.disease_name
          ? `${character.health.disease_name} (${character.health.severity})`
          : t('bunker.healthy')
      case 'hobby':
        if (!character.hobby) return t('common.none')
        return `${character.hobby.name} (${character.hobby.experience_level}) — ${character.hobby.category}`
      case 'phobia':
        return character.phobia?.name ?? t('common.none')
      case 'backpack_item':
        return character.backpack_item?.name ?? t('common.none')
      case 'large_item':
        return character.large_item?.name ?? t('common.none')
      case 'trait':
        return character.trait ? `${character.trait.trait} — ${character.trait.category}` : t('common.none')
      case 'additional_info':
        return character.additional_info?.name ?? t('common.none')
      default:
        return t('common.none')
    }
  }

  useEffect(() => {
    if (!token) return
    const load = () => {
      fetchPublicBunker(token)
        .then((s) => {
          setState(s)
          setError('')
          if (s.language === 'en' || s.language === 'ru') setPageLang(s.language)
        })
        .catch(() => setError(t('publicBunker.errorInvalid')))
    }
    load()
    const timer = setInterval(load, 4000)
    return () => clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- poll by token; error text uses pageLang
  }, [token, pageLang])

  const remaining = useCountdown(state?.phase_deadline_ts ?? null)
  const timerUrgent = remaining > 0 && remaining <= 30

  const voteOptions = useMemo(() => {
    if (!state) return []
    const options = state.alive_players.map((p) => ({ id: p.user_id, name: p.display_name }))
    return [{ id: '', name: t('game.skip') }, ...options]
  }, [state, pageLang])

  const abilityTargetOptions = useMemo(() => {
    if (!state) return []
    const options = state.roster.map((p) => ({
      id: p.user_id,
      name: `${p.display_name}${p.alive ? '' : t('publicBunker.eliminatedSuffix')}`,
    }))
    return [{ id: '', name: t('publicBunker.noTarget') }, ...options]
  }, [state, pageLang])

  const submitVote = async () => {
    if (!token) return
    setVoteBusy(true)
    setVoteMessage('')
    try {
      await submitBunkerVote(token, voteTarget || null)
      setVoteMessage(t('game.sent'))
      const refreshed = await fetchPublicBunker(token)
      setState(refreshed)
    } catch {
      setVoteMessage(t('game.sendFailed'))
    } finally {
      setVoteBusy(false)
    }
  }

  const reveal = async (key: BunkerFieldKey) => {
    if (!token) return
    try {
      await revealBunkerFields(token, [key])
      const refreshed = await fetchPublicBunker(token)
      setState(refreshed)
    } catch {
      setError(t('publicBunker.revealFailed'))
    }
  }

  const openAbilityForm = (index: 1 | 2) => {
    setAbilityCardIndex(index)
    setAbilityTarget('')
    setAbilityNote('')
    setAbilityMessage('')
  }

  const submitAbility = async () => {
    if (!token || !abilityCardIndex) return
    setAbilityBusy(true)
    setAbilityMessage('')
    try {
      await announceBunkerAbility(token, abilityCardIndex, abilityTarget || null, abilityNote)
      setAbilityMessage(t('publicBunker.abilitySent'))
      setAbilityCardIndex(null)
      const refreshed = await fetchPublicBunker(token)
      setState(refreshed)
    } catch {
      setAbilityMessage(t('publicBunker.abilitySendFailed'))
    } finally {
      setAbilityBusy(false)
    }
  }

  if (error) {
    return (
      <div className="game-table game-table--bunker flex min-h-dvh items-center justify-center p-6">
        <p className="text-sm text-danger">{error}</p>
      </div>
    )
  }

  if (!state) {
    return (
      <div className="game-table game-table--bunker flex min-h-dvh items-center justify-center p-6">
        <p className="text-sm text-muted">{t('common.loading')}</p>
      </div>
    )
  }

  const character = state.your_character
  const aliveCount = state.roster.filter((p) => p.alive).length
  const canReveal = state.phase === 'discussion' && state.your_alive && state.game_status === 'active'
  const canUseAbility = state.your_alive && state.game_status === 'active' && state.phase !== 'vote'
  const timerText = formatTimer(remaining)

  return (
    <div className="game-table game-table--bunker min-h-dvh">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6">
        <header className="game-hud animate-fade-in-up sticky top-3 z-10 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-card)] border border-border/70 px-4 py-3 backdrop-blur-md">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">{t('publicBunker.title')}</p>
            <h1 className="truncate text-lg font-semibold text-foreground sm:text-xl">
              {t('game.round', { round: state.round_number })} · {phaseLabel(state.phase) ?? state.phase}
            </h1>
          </div>
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
        </header>

        <section className="game-panel animate-fade-in-up flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/70 p-4" style={{ animationDelay: '60ms' }}>
          <div className="flex flex-wrap gap-2 text-xs">
            {state.bunker_capacity && (
              <span className="game-chip inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-foreground">
                <UsersThree size={14} weight="fill" className="text-primary" />
                {t('publicBunker.capacity')} {state.bunker_capacity} {t('publicBunker.capacityOf', { total: state.roster.length })}
              </span>
            )}
          </div>
          {state.catastrophe_name && (
            <div className="rounded-control border border-danger/25 bg-danger/5 px-3 py-2.5">
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-danger">
                <Warning size={14} weight="fill" />
                {t('publicBunker.catastrophe', { name: state.catastrophe_name })}
              </p>
              <p className="mt-1 text-sm text-muted">{state.catastrophe_description}</p>
            </div>
          )}
          {state.bunker_conditions_name && (
            <div className="rounded-control border border-border/80 bg-background/40 px-3 py-2.5">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                {t('publicBunker.bunkerConditions', { name: state.bunker_conditions_name })}
              </p>
              <p className="mt-1 text-sm text-foreground/90">{state.bunker_conditions_description}</p>
            </div>
          )}
          {!state.your_alive && (
            <p className="flex items-center gap-2 text-sm text-danger">
              <Skull size={16} weight="fill" />
              {t('game.eliminatedBunker')}
            </p>
          )}
          {state.game_status !== 'active' && (
            <p className="text-sm text-muted">
              {state.game_status === 'finished' ? t('game.finished') : t('game.cancelled')}
            </p>
          )}
        </section>

        {character && (
          <section className="game-panel animate-fade-in-up flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/70 p-4" style={{ animationDelay: '120ms' }}>
            <div className="flex items-center gap-2">
              <IdentificationCard size={18} weight="fill" className="text-primary" />
              <h2 className="text-sm font-semibold text-foreground">{t('publicBunker.yourCard')}</h2>
            </div>
            <ul className="grid gap-2">
              {BUNKER_FIELD_KEYS.map((key) => {
                const revealed = state.your_revealed_fields.includes(key)
                return (
                  <li
                    key={key}
                    className={`flex items-center justify-between gap-3 rounded-control border px-3 py-2.5 transition-colors ${
                      revealed ? 'border-primary/35 bg-primary-muted/40' : 'border-border/70 bg-background/35'
                    }`}
                  >
                    <div className="flex min-w-0 items-start gap-2.5">
                      <span className="mt-0.5 text-primary">{FIELD_ICON[key]}</span>
                      <div className="min-w-0">
                        <p className="text-xs text-muted">
                          {fieldLabel(key)}
                          {revealed && <span className="ml-1.5 text-primary">{t('publicBunker.revealed')}</span>}
                        </p>
                        <p className="text-sm text-foreground">{fieldValue(key, character)}</p>
                      </div>
                    </div>
                    {!revealed && canReveal && (
                      <Button variant="secondary" onClick={() => reveal(key)}>
                        {t('publicBunker.reveal')}
                      </Button>
                    )}
                  </li>
                )
              })}
            </ul>
          </section>
        )}

        {character?.special_abilities && character.special_abilities.length > 0 && (
          <section className="game-panel flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/70 p-4">
            <div className="flex items-center gap-2">
              <Lightning size={18} weight="fill" className="text-warning" />
              <h2 className="text-sm font-semibold text-foreground">{t('publicBunker.specialAbilities')}</h2>
            </div>
            <ul className="flex flex-col gap-3 text-sm">
              {character.special_abilities.map((card, index) => {
                const cardIndex = (index + 1) as 1 | 2
                return (
                  <li key={index} className="rounded-control border border-border/70 bg-background/35 px-3 py-3">
                    <p className="text-foreground">
                      <span className="font-medium">{card.name}</span> — {card.category}
                    </p>
                    <p className="mt-1 text-xs text-muted">{card.effect}</p>
                    {card.used ? (
                      <span className="mt-2 inline-block text-xs text-muted">{t('publicBunker.abilityUsed')}</span>
                    ) : abilityCardIndex === cardIndex ? (
                      <div className="mt-3 flex flex-col gap-2">
                        <Select
                          value={abilityTarget}
                          onChange={setAbilityTarget}
                          options={abilityTargetOptions}
                          placeholder={t('publicBunker.abilityTargetPlaceholder')}
                        />
                        <input
                          value={abilityNote}
                          onChange={(e) => setAbilityNote(e.target.value)}
                          placeholder={t('publicBunker.abilityNotePlaceholder')}
                          maxLength={300}
                          className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                        />
                        <div className="flex gap-2">
                          <Button variant="secondary" onClick={() => setAbilityCardIndex(null)}>
                            {t('common.cancel')}
                          </Button>
                          <Button variant="primary" onClick={submitAbility} disabled={abilityBusy}>
                            {abilityBusy ? t('game.sending') : t('publicBunker.abilityAnnounce')}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      canUseAbility && (
                        <div className="mt-2">
                          <Button variant="secondary" onClick={() => openAbilityForm(cardIndex)}>
                            {t('publicBunker.useAbility')}
                          </Button>
                        </div>
                      )
                    )}
                  </li>
                )
              })}
            </ul>
            {abilityMessage && <p className="text-sm text-primary">{abilityMessage}</p>}
          </section>
        )}

        {state.action_required && (
          <section className="game-panel game-panel--action flex flex-col gap-3 rounded-[var(--radius-card)] border border-primary/40 p-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-foreground">{t('publicBunker.voteTitle')}</h2>
              <span className={`font-mono text-sm tabular-nums ${timerUrgent ? 'text-danger' : 'text-muted'}`}>
                {timerText}
              </span>
            </div>
            <Select
              value={voteTarget}
              onChange={setVoteTarget}
              options={voteOptions}
              placeholder={t('publicBunker.excludeWho')}
            />
            <Button variant="primary" onClick={submitVote} disabled={voteBusy}>
              {voteBusy ? t('game.sending') : state.your_vote_submitted ? t('game.changeChoice') : t('game.submit')}
            </Button>
            {state.your_vote_submitted && (
              <p className="text-xs text-muted">{t('publicBunker.voteSent')}</p>
            )}
            {voteMessage && <p className="text-sm text-primary">{voteMessage}</p>}
          </section>
        )}

        {state.phase === 'vote' && state.vote_tally && state.vote_tally.length > 0 && (
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
          <ul className="grid gap-2 sm:grid-cols-2">
            {state.roster.map((p) => {
              const revealedKeys = BUNKER_FIELD_KEYS.filter((key) => key in p.character)
              return (
                <li
                  key={p.user_id}
                  className={`rounded-control border px-3 py-3 ${
                    p.alive ? 'border-border/70 bg-background/35' : 'border-border/40 bg-background/20'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <GameAvatar name={p.display_name} avatarUrl={p.avatar_url} alive={p.alive} size="md" />
                    <div className="min-w-0">
                      <p className={`truncate text-sm font-medium ${p.alive ? 'text-foreground' : 'text-muted line-through'}`}>
                        {p.display_name}
                        {!p.alive && ' 💀'}
                      </p>
                      {!p.alive && (
                        <p className="text-[11px] uppercase tracking-wide text-danger">{t('game.eliminatedBunker')}</p>
                      )}
                    </div>
                  </div>
                  {revealedKeys.length > 0 && (
                    <ul className="mt-2 flex flex-col gap-0.5 border-t border-border/50 pt-2 text-xs text-muted">
                      {revealedKeys.map((key) => (
                        <li key={key} className="flex items-start gap-1.5">
                          <span className="mt-0.5 text-primary/80">{FIELD_ICON[key]}</span>
                          <span>
                            {fieldLabel(key)}: {fieldValue(key, p.character)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              )
            })}
          </ul>
        </section>

        {!state.action_required && state.your_alive && state.game_status === 'active' && state.phase === 'discussion' && (
          <p className="text-center text-sm text-muted">{t('publicBunker.discussHint')}</p>
        )}
      </div>
    </div>
  )
}
