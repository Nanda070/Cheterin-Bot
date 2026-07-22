import { useState } from 'react'
import { useT } from '../context/LanguageContext'
import type { BunkerCardPools, BunkerCharacter, BunkerPlayerRef } from '../api/client'
import {
  isBunkerHealthy,
  isBunkerHealthySeverity,
  isBunkerRelationshipCategory,
  substituteBunkerRelationshipPlayer,
} from '../config/bunkerMarkers'
import { Button } from '../components/ui/Button'
import { Select, type SelectOption } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

interface Props {
  character: BunkerCharacter
  pools: BunkerCardPools
  roster: BunkerPlayerRef[]
  currentUserId: string
  onSave: (character: BunkerCharacter) => void
  onCancel: () => void
  busy?: boolean
}

const labelClass = 'text-xs text-muted'
const rowClass = 'flex flex-col gap-1'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className={rowClass}>
      <label className={labelClass}>{label}</label>
      {children}
    </div>
  )
}

export function BunkerCharacterEditor({ character, pools, roster, currentUserId, onSave, onCancel, busy }: Props) {
  const t = useT()
  const [draft, setDraft] = useState<BunkerCharacter>(() => JSON.parse(JSON.stringify(character)))

  const professionOptions: SelectOption[] = pools.professions.map((p) => ({
    id: String(p.id), name: p.name, category: p.category,
  }))
  const professionLevelOptions: SelectOption[] = pools.profession_experience_levels.map((l) => ({
    id: l.level, name: l.level,
  }))
  const ageOptions: SelectOption[] = pools.ages.map((a) => ({ id: a.key, name: a.label }))
  const genderOptions: SelectOption[] = pools.genders.map((g) => ({ id: g, name: g }))
  const bodyTypeOptions: SelectOption[] = pools.body_types.map((b) => ({ id: b.key, name: b.name }))
  const healthSeverityOptions: SelectOption[] = pools.health_severities.map((s) => ({ id: s, name: s }))
  const diseaseOptions: SelectOption[] = pools.health_diseases.map((d) => ({
    id: String(d.id), name: d.name, category: d.category,
  }))
  const hobbyOptions: SelectOption[] = pools.hobbies.map((h) => ({ id: String(h.id), name: h.name, category: h.category }))
  const hobbyLevelOptions: SelectOption[] = pools.hobby_experience_levels.map((l) => ({ id: l.level, name: l.level }))
  const phobiaOptions: SelectOption[] = pools.phobias.map((p) => ({ id: String(p.id), name: p.name, category: p.type }))
  const backpackOptions: SelectOption[] = pools.backpack_items.map((i) => ({ id: String(i.id), name: i.name, category: i.category }))
  const largeItemOptions: SelectOption[] = pools.large_items.map((i) => ({ id: String(i.id), name: i.name, category: i.category }))
  const traitOptions: SelectOption[] = pools.traits.map((t) => ({ id: t.trait, name: t.trait, category: t.category }))
  const additionalInfoOptions: SelectOption[] = pools.additional_info.map((a) => ({
    id: String(a.id), name: a.name, category: a.category,
  }))
  const abilityOptions: SelectOption[] = pools.special_abilities.map((a) => ({
    id: String(a.id), name: a.name, category: a.category,
  }))
  const targetOptions: SelectOption[] = roster
    .filter((p) => p.user_id !== currentUserId)
    .map((p) => ({ id: p.user_id, name: p.display_name }))

  const isRelationshipCard = isBunkerRelationshipCategory(draft.additional_info?.category)

  const patch = (updater: (prev: BunkerCharacter) => BunkerCharacter) => setDraft(updater)

  return (
    <div className="flex max-h-[70vh] flex-col gap-4 overflow-y-auto pr-1">
      <Field label={t('bunker.editor.profession')}>
        <Select
          value={draft.profession ? String(pools.professions.find((p) => p.name === draft.profession!.name)?.id ?? '') : ''}
          onChange={(id) => {
            const picked = pools.professions.find((p) => String(p.id) === id)
            if (!picked) return
            patch((prev) => ({
              ...prev,
              profession: {
                name: picked.name, category: picked.category,
                experience_level: prev.profession?.experience_level ?? pools.profession_experience_levels[0].level,
                has_ability: prev.profession?.has_ability ?? false,
              },
            }))
          }}
          options={professionOptions}
        />
        <Select
          value={draft.profession?.experience_level ?? ''}
          onChange={(level) => {
            const picked = pools.profession_experience_levels.find((l) => l.level === level)
            patch((prev) => (prev.profession ? { ...prev, profession: { ...prev.profession, experience_level: level, has_ability: picked?.has_ability ?? false } } : prev))
          }}
          options={professionLevelOptions}
          placeholder={t('bunker.editor.experience')}
        />
      </Field>

      <Field label={t('bunker.editor.age')}>
        <Select
          value={draft.age?.key ?? ''}
          onChange={(key) => {
            const picked = pools.ages.find((a) => a.key === key)
            if (picked) patch((prev) => ({ ...prev, age: { key: picked.key, label: picked.label } }))
          }}
          options={ageOptions}
        />
      </Field>

      <Field label={t('bunker.editor.gender')}>
        <Select value={draft.gender ?? ''} onChange={(g) => patch((prev) => ({ ...prev, gender: g }))} options={genderOptions} />
      </Field>

      <Field label={t('bunker.editor.bodyType')}>
        <Select
          value={draft.body_type?.key ?? ''}
          onChange={(key) => {
            const picked = pools.body_types.find((b) => b.key === key)
            if (picked) patch((prev) => ({ ...prev, body_type: picked }))
          }}
          options={bodyTypeOptions}
        />
      </Field>

      <Field label={t('bunker.editor.health')}>
        <Select
          value={draft.health?.severity ?? ''}
          onChange={(severity) =>
            patch((prev) => ({
              ...prev,
              health: isBunkerHealthySeverity(severity)
                ? { severity, disease_name: null, category: null }
                : { severity, disease_name: prev.health?.disease_name ?? null, category: prev.health?.category ?? null },
            }))
          }
          options={healthSeverityOptions}
        />
        {draft.health && !isBunkerHealthySeverity(draft.health.severity) && (
          <Select
            value={draft.health.disease_name ? String(pools.health_diseases.find((d) => d.name === draft.health!.disease_name)?.id ?? '') : ''}
            onChange={(id) => {
              const picked = pools.health_diseases.find((d) => String(d.id) === id)
              if (picked) patch((prev) => (prev.health ? { ...prev, health: { ...prev.health, disease_name: picked.name, category: picked.category } } : prev))
            }}
            options={diseaseOptions}
            placeholder={t('bunker.editor.diagnosis')}
          />
        )}
      </Field>

      <Field label={t('bunker.editor.hobby')}>
        <Select
          value={draft.hobby ? String(pools.hobbies.find((h) => h.name === draft.hobby!.name)?.id ?? '') : ''}
          onChange={(id) => {
            const picked = pools.hobbies.find((h) => String(h.id) === id)
            if (!picked) return
            patch((prev) => ({
              ...prev,
              hobby: { name: picked.name, category: picked.category, experience_level: prev.hobby?.experience_level ?? pools.hobby_experience_levels[0].level },
            }))
          }}
          options={hobbyOptions}
        />
        <Select
          value={draft.hobby?.experience_level ?? ''}
          onChange={(level) => patch((prev) => (prev.hobby ? { ...prev, hobby: { ...prev.hobby, experience_level: level } } : prev))}
          options={hobbyLevelOptions}
          placeholder={t('bunker.editor.level')}
        />
      </Field>

      <Field label={t('bunker.editor.phobia')}>
        <Select
          value={draft.phobia ? String(pools.phobias.find((p) => p.name === draft.phobia!.name)?.id ?? '') : ''}
          onChange={(id) => {
            const picked = pools.phobias.find((p) => String(p.id) === id)
            if (picked) patch((prev) => ({ ...prev, phobia: { name: picked.name, type: picked.type } }))
          }}
          options={phobiaOptions}
        />
      </Field>

      <Field label={t('bunker.editor.backpack')}>
        <Select
          value={draft.backpack_item ? String(pools.backpack_items.find((i) => i.name === draft.backpack_item!.name)?.id ?? '') : ''}
          onChange={(id) => {
            const picked = pools.backpack_items.find((i) => String(i.id) === id)
            if (picked) patch((prev) => ({ ...prev, backpack_item: { name: picked.name, category: picked.category } }))
          }}
          options={backpackOptions}
        />
      </Field>

      <Field label={t('bunker.editor.largeItem')}>
        <Select
          value={draft.large_item ? String(pools.large_items.find((i) => i.name === draft.large_item!.name)?.id ?? '') : ''}
          onChange={(id) => {
            const picked = pools.large_items.find((i) => String(i.id) === id)
            if (picked) patch((prev) => ({ ...prev, large_item: { name: picked.name, category: picked.category } }))
          }}
          options={largeItemOptions}
        />
      </Field>

      <Field label={t('bunker.editor.trait')}>
        <Select
          value={draft.trait?.trait ?? ''}
          onChange={(traitName) => {
            const picked = pools.traits.find((t) => t.trait === traitName)
            if (picked) patch((prev) => ({ ...prev, trait: picked }))
          }}
          options={traitOptions}
        />
      </Field>

      <Field label={t('bunker.editor.additionalInfo')}>
        {draft.additional_info && <p className="text-sm text-foreground">{draft.additional_info.name}</p>}
        <Select
          value={draft.additional_info ? String(pools.additional_info.find((a) => a.name === draft.additional_info!.name)?.id ?? '') : ''}
          onChange={(id) => {
            const picked = pools.additional_info.find((a) => String(a.id) === id)
            if (!picked) return
            if (isBunkerRelationshipCategory(picked.category)) {
              // Свежий шаблон карты «Отношения» — сразу подставляем первого доступного игрока-цель,
              // чтобы плейсхолдер «Игрок №X» / «Player #X» никогда не попадал в сохранённую карточку.
              const firstTarget = targetOptions[0]
              const name = firstTarget ? substituteBunkerRelationshipPlayer(picked.name, firstTarget.name) : picked.name
              patch((prev) => ({
                ...prev,
                additional_info: { name, category: picked.category, linked_user_id: firstTarget ? firstTarget.id : null },
              }))
            } else {
              patch((prev) => ({ ...prev, additional_info: { name: picked.name, category: picked.category, linked_user_id: null } }))
            }
          }}
          options={additionalInfoOptions}
          placeholder={t('bunker.editor.selectNewCard')}
        />
        {isRelationshipCard && (
          <Select
            value={draft.additional_info?.linked_user_id ?? ''}
            onChange={(targetId) => {
              const newTarget = roster.find((p) => p.user_id === targetId)
              if (!newTarget) return
              patch((prev) => {
                if (!prev.additional_info) return prev
                const oldTarget = roster.find((p) => p.user_id === prev.additional_info!.linked_user_id)
                const name = oldTarget
                  ? prev.additional_info.name.split(oldTarget.display_name).join(newTarget.display_name)
                  : prev.additional_info.name
                return { ...prev, additional_info: { ...prev.additional_info, name, linked_user_id: targetId } }
              })
            }}
            options={targetOptions}
            placeholder={t('bunker.editor.targetPlayer')}
          />
        )}
      </Field>

      <div className="flex flex-col gap-2 border-t border-border pt-3">
        <p className="text-xs font-medium text-foreground">{t('bunker.editor.specialAbilities')}</p>
        {[0, 1].map((index) => {
          const card = draft.special_abilities?.[index]
          return (
            <div key={index} className="flex flex-col gap-1.5 rounded-control border border-border p-2">
              <Select
                value={card ? String(pools.special_abilities.find((a) => a.name === card.name)?.id ?? '') : ''}
                onChange={(id) => {
                  const picked = pools.special_abilities.find((a) => String(a.id) === id)
                  if (!picked) return
                  patch((prev) => {
                    const abilities = [...(prev.special_abilities ?? [{ name: '', category: '', effect: '', used: false }, { name: '', category: '', effect: '', used: false }])]
                    abilities[index] = { name: picked.name, category: picked.category, effect: picked.effect, used: abilities[index]?.used ?? false }
                    return { ...prev, special_abilities: abilities }
                  })
                }}
                options={abilityOptions}
              />
              <Toggle
                checked={card?.used ?? false}
                onChange={(used) =>
                  patch((prev) => {
                    if (!prev.special_abilities) return prev
                    const abilities = [...prev.special_abilities]
                    abilities[index] = { ...abilities[index], used }
                    return { ...prev, special_abilities: abilities }
                  })
                }
                label={t('bunker.editor.used')}
              />
            </div>
          )
        })}
      </div>

      <div className="flex justify-end gap-2 border-t border-border pt-3">
        <Button variant="secondary" onClick={onCancel}>
          {t('common.cancel')}
        </Button>
        <Button variant="primary" onClick={() => onSave(draft)} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
