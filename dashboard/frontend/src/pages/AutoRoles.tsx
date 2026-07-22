import { useEffect, useState } from 'react'
import { fetchAutoRoles, fetchRoles, updateAutoRoles, type RoleInfo } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Checkbox } from '../components/ui/Checkbox'
import { useT } from '../context/LanguageContext'

export function AutoRolesPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchRoles(), fetchAutoRoles()])
      .then(([roleList, settings]) => {
        setRoles(roleList)
        setSelectedRoleIds(settings.role_ids)
      })
      .catch(() => setError(t('autoRoles.errorLoad')))
      .finally(() => setLoading(false))
  }, [t])

  const toggleRole = (roleId: string) => {
    setSelectedRoleIds((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId],
    )
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateAutoRoles(selectedRoleIds)
      setSelectedRoleIds(updated.role_ids)
      setSavedMessage(t('common.saved'))
    } catch {
      setError(t('autoRoles.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return <p className="text-sm text-muted">{t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-xl flex-col gap-4">
      {!embedded && <h1 className="text-lg font-semibold text-foreground">{t('autoRoles.title')}</h1>}
      {embedded && <h2 className="font-semibold text-foreground">{t('autoRoles.title')}</h2>}

      <Card className="flex flex-col gap-3">
        <p className="text-sm text-muted">{t('autoRoles.intro')}</p>
        <div className="flex flex-wrap gap-3">
          {roles.map((r) => (
            <Checkbox
              key={r.id}
              checked={selectedRoleIds.includes(r.id)}
              onChange={() => toggleRole(r.id)}
              label={r.name}
            />
          ))}
        </div>
      </Card>

      {error && <p className="text-sm text-danger">{error}</p>}
      {savedMessage && <p className="text-sm text-primary">{savedMessage}</p>}

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
