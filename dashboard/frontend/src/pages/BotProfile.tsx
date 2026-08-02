import { IdentificationCard, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchBotProfile,
  updateBotProfile,
  type BotProfileResponse,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

async function fileToDataUri(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

export function BotProfilePage() {
  const t = useT()
  const [profile, setProfile] = useState<BotProfileResponse | null>(null)
  const [nick, setNick] = useState('')
  const [avatarData, setAvatarData] = useState<string | null | undefined>(undefined)
  const [bannerData, setBannerData] = useState<string | null | undefined>(undefined)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [bannerPreview, setBannerPreview] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  const reload = () =>
    fetchBotProfile()
      .then((data) => {
        setProfile(data)
        setNick(data.nick)
        setAvatarPreview(data.avatar_url)
        setBannerPreview(data.banner_url)
        setAvatarData(undefined)
        setBannerData(undefined)
        setError('')
      })
      .catch((err) => setError(formatApiError(err, t, 'botProfile.errorLoad')))

  useEffect(() => {
    reload()
  }, [t])

  const onAvatarFile = async (file: File | null) => {
    if (!file) return
    try {
      const uri = await fileToDataUri(file)
      setAvatarData(uri)
      setAvatarPreview(uri)
    } catch {
      setError(t('botProfile.errorImage'))
    }
  }

  const onBannerFile = async (file: File | null) => {
    if (!file) return
    try {
      const uri = await fileToDataUri(file)
      setBannerData(uri)
      setBannerPreview(uri)
    } catch {
      setError(t('botProfile.errorImage'))
    }
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const body: { nick?: string | null; avatar?: string | null; banner?: string | null } = {
        nick,
      }
      if (avatarData !== undefined) body.avatar = avatarData
      if (bannerData !== undefined) body.banner = bannerData
      const updated = await updateBotProfile(body)
      setProfile(updated)
      setNick(updated.nick)
      setAvatarPreview(updated.avatar_url)
      setBannerPreview(updated.banner_url)
      setAvatarData(undefined)
      setBannerData(undefined)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'botProfile.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (!profile) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <IdentificationCard size={22} className="text-primary" />
          {t('botProfile.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('botProfile.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex flex-col items-center gap-2">
            {avatarPreview ? (
              <img
                src={avatarPreview}
                alt=""
                className="h-20 w-20 rounded-full object-cover ring-1 ring-border"
              />
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-surface-hover text-xs text-muted">
                {t('botProfile.noAvatar')}
              </div>
            )}
            <label className="cursor-pointer text-xs text-primary hover:underline">
              {t('botProfile.uploadAvatar')}
              <input
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                className="hidden"
                onChange={(e) => onAvatarFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <button
              type="button"
              className="flex items-center gap-1 text-xs text-muted hover:text-danger"
              onClick={() => {
                setAvatarData(null)
                setAvatarPreview(null)
              }}
            >
              <Trash size={12} />
              {t('botProfile.clearAvatar')}
            </button>
          </div>

          <div className="min-w-0 flex-1 flex flex-col gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="bp-nick">
                {t('botProfile.nick')}
              </label>
              <input
                id="bp-nick"
                maxLength={32}
                value={nick}
                onChange={(e) => setNick(e.target.value)}
                className={inputClass}
                placeholder={profile.display_name}
              />
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted">{t('botProfile.banner')}</span>
              {bannerPreview ? (
                <img
                  src={bannerPreview}
                  alt=""
                  className="h-24 w-full max-w-md rounded-control object-cover ring-1 ring-border"
                />
              ) : (
                <div className="flex h-24 max-w-md items-center justify-center rounded-control bg-surface-hover text-xs text-muted">
                  {t('botProfile.noBanner')}
                </div>
              )}
              <div className="flex flex-wrap gap-3">
                <label className="cursor-pointer text-xs text-primary hover:underline">
                  {t('botProfile.uploadBanner')}
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/gif,image/webp"
                    className="hidden"
                    onChange={(e) => onBannerFile(e.target.files?.[0] ?? null)}
                  />
                </label>
                <button
                  type="button"
                  className="flex items-center gap-1 text-xs text-muted hover:text-danger"
                  onClick={() => {
                    setBannerData(null)
                    setBannerPreview(null)
                  }}
                >
                  <Trash size={12} />
                  {t('botProfile.clearBanner')}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
