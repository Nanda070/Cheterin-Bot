import { useEffect, useMemo, useState } from 'react'
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
  const character = state.your_character
  const aliveCount = state.roster.filter((p) => p.alive).length
  const canReveal = state.phase === 'discussion' && state.your_alive && state.game_status === 'active'
  const canUseAbility = state.your_alive && state.game_status === 'active' && state.phase !== 'vote'

  return (
    <div className="flex min-h-dvh flex-col items-center bg-background p-6">
      <div className="flex w-full max-w-lg flex-col gap-4">
        <h1 className="text-lg font-semibold text-foreground">{t('publicBunker.title')}</h1>

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
          {state.bunker_capacity && (
            <p className="text-sm text-muted">
              {t('publicBunker.capacity')}{' '}
              <span className="text-foreground">{state.bunker_capacity}</span>{' '}
              {t('publicBunker.capacityOf', { total: state.roster.length })}
            </p>
          )}
          {state.catastrophe_name && (
            <p className="text-sm text-muted">
              <span className="font-medium text-foreground">
                {t('publicBunker.catastrophe', { name: state.catastrophe_name })}
              </span>{' '}
              {state.catastrophe_description}
            </p>
          )}
          {state.bunker_conditions_name && (
            <p className="text-sm text-muted">
              <span className="font-medium text-foreground">
                {t('publicBunker.bunkerConditions', { name: state.bunker_conditions_name })}
              </span>{' '}
              {state.bunker_conditions_description}
            </p>
          )}
          {!state.your_alive && <p className="text-sm text-danger">{t('game.eliminatedBunker')}</p>}
          {state.game_status !== 'active' && (
            <p className="text-sm text-muted">
              {state.game_status === 'finished' ? t('game.finished') : t('game.cancelled')}
            </p>
          )}
        </Card>

        {character && (
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-foreground">{t('publicBunker.yourCard')}</h2>
            <ul className="flex flex-col gap-2 text-sm">
              {BUNKER_FIELD_KEYS.map((key) => {
                const revealed = state.your_revealed_fields.includes(key)
                return (
                  <li key={key} className="flex items-center justify-between gap-3 border-b border-border pb-2 last:border-0 last:pb-0">
                    <div>
                      <p className="text-xs text-muted">
                        {fieldLabel(key)}
                        {revealed && <span className="ml-1.5 text-primary">{t('publicBunker.revealed')}</span>}
                      </p>
                      <p className="text-foreground">{fieldValue(key, character)}</p>
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
          </Card>
        )}

        {character?.special_abilities && character.special_abilities.length > 0 && (
          <Card className="flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-foreground">{t('publicBunker.specialAbilities')}</h2>
            <ul className="flex flex-col gap-3 text-sm">
              {character.special_abilities.map((card, index) => {
                const cardIndex = (index + 1) as 1 | 2
                return (
                  <li key={index} className="flex flex-col gap-1.5 border-b border-border pb-3 last:border-0 last:pb-0">
                    <p className="text-foreground">
                      <span className="font-medium">{card.name}</span> — {card.category}
                    </p>
                    <p className="text-xs text-muted">{card.effect}</p>
                    {card.used ? (
                      <span className="text-xs text-muted">{t('publicBunker.abilityUsed')}</span>
                    ) : abilityCardIndex === cardIndex ? (
                      <div className="flex flex-col gap-2">
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
                        <div>
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
          </Card>
        )}

        {state.action_required && (
          <Card className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">{t('publicBunker.voteTitle')}</h2>
              <span className="text-sm text-muted">
                {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
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
          </Card>
        )}

        {state.phase === 'vote' && state.vote_tally && state.vote_tally.length > 0 && (
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
          <ul className="flex flex-col gap-2 text-sm">
            {state.roster.map((p) => {
              const revealedKeys = BUNKER_FIELD_KEYS.filter((key) => key in p.character)
              return (
                <li key={p.user_id} className={p.alive ? 'text-foreground' : 'text-muted'}>
                  <p className={p.alive ? '' : 'line-through'}>
                    {p.display_name}
                    {!p.alive && ' 💀'}
                  </p>
                  {revealedKeys.length > 0 && (
                    <ul className="ml-3 flex flex-col gap-0.5 text-xs text-muted">
                      {revealedKeys.map((key) => (
                        <li key={key}>
                          {fieldLabel(key)}: {fieldValue(key, p.character)}
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              )
            })}
          </ul>
        </Card>

        {!state.action_required && state.your_alive && state.game_status === 'active' && state.phase === 'discussion' && (
          <p className="text-sm text-muted">{t('publicBunker.discussHint')}</p>
        )}
      </div>
    </div>
  )
}
