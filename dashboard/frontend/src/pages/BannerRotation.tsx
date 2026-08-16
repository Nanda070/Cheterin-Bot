import { Image, Trash } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import {
  ApiError,
  deleteBannerRotationImage,
  fetchBannerRotationSettings,
  fetchChannels,
  triggerBannerRotation,
  updateBannerRotationSettings,
  uploadBannerRotationImage,
  type BannerRotationImage,
  type BannerRotationSettings,
  type ChannelInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

function formatTs(ts: number, t: (k: string) => string): string {
  if (!ts) return t('bannerRotation.neverRotated')
  return new Date(ts * 1000).toLocaleString()
}

function ImageGrid({
  images,
  onDelete,
  t,
}: {
  images: BannerRotationImage[]
  onDelete: (id: string) => void
  t: (k: string) => string
}) {
  if (images.length === 0) return <p className="text-sm text-muted">{t('bannerRotation.noImages')}</p>
  return (
    <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {images.map((img) => (
        <div key={img.id} className="group relative overflow-hidden rounded-control border border-border bg-surface">
          <img
            src={img.url}
            alt={img.original_name}
            className="h-28 w-full object-cover"
            loading="lazy"
          />
          <div className="flex items-center justify-between gap-1 px-2 py-1.5">
            <span className="truncate text-xs text-muted" title={img.original_name}>
              {img.original_name}
            </span>
            <button
              type="button"
              onClick={() => onDelete(img.id)}
              className="shrink-0 text-muted hover:text-danger"
              aria-label={t('bannerRotation.delete')}
            >
              <Trash size={14} />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

function UploadZone({
  onFiles,
  uploading,
  t,
  disabled,
}: {
  onFiles: (files: File[]) => void
  uploading: boolean
  t: (k: string) => string
  disabled?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  return (
    <div>
      <label
        className={`text-xs ${disabled ? 'cursor-not-allowed text-muted' : 'cursor-pointer text-primary hover:underline'}`}
      >
        {uploading ? t('bannerRotation.uploading') : t('bannerRotation.upload')}
        <input
          ref={inputRef}
          type="file"
          multiple
          accept="image/png,image/jpeg,image/gif,image/webp"
          className="hidden"
          disabled={uploading || disabled}
          onChange={(e) => {
            const files = Array.from(e.target.files || [])
            if (files.length) onFiles(files)
            if (inputRef.current) inputRef.current.value = ''
          }}
        />
      </label>
      <p className="mt-0.5 text-xs text-muted">{t('bannerRotation.uploadHint')}</p>
    </div>
  )
}

export function BannerRotationPage() {
  const t = useT()
  const [settings, setSettings] = useState<BannerRotationSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [uploadingBanners, setUploadingBanners] = useState(false)
  const [uploadingIcons, setUploadingIcons] = useState(false)
  const [rotating, setRotating] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const reload = () => {
    fetchBannerRotationSettings()
      .then((cfg) =>
        setSettings({
          ...cfg,
          banner_mode: cfg.banner_mode === 'both' ? 'both' : cfg.banner_mode === 'dynamic' ? 'dynamic' : 'playlist',
        }),
      )
      .catch(() => setError(t('bannerRotation.errorLoad')))
    fetchChannels()
      .then(setChannels)
      .catch(() => setChannels([]))
  }

  useEffect(reload, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const channelOptions = [
    { id: '', name: t('bannerRotation.logChannelNone') },
    ...channels,
  ]

  const bannerModeOptions = [
    { id: 'playlist', name: t('bannerRotation.bannerMode.playlist') },
    { id: 'dynamic', name: t('bannerRotation.bannerMode.dynamic') },
    { id: 'both', name: t('bannerRotation.bannerMode.both') },
  ]

  const dynamicMode = settings.banner_mode === 'dynamic' || settings.banner_mode === 'both'

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateBannerRotationSettings({
        enabled: settings.enabled,
        banner_enabled: settings.banner_enabled,
        banner_mode: settings.banner_mode,
        dynamic_window_days: settings.dynamic_window_days,
        icon_enabled: settings.icon_enabled,
        interval_minutes: settings.interval_minutes,
        log_channel_id: settings.log_channel_id,
      })
      setSettings({
        ...updated,
        banner_mode: updated.banner_mode === 'both' ? 'both' : updated.banner_mode === 'dynamic' ? 'dynamic' : 'playlist',
      })
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'bannerRotation.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const uploadImages = async (kind: 'banner' | 'icon', files: File[]) => {
    const setter = kind === 'banner' ? setUploadingBanners : setUploadingIcons
    setter(true)
    setUploadError('')
    try {
      for (const file of files) {
        await uploadBannerRotationImage(kind, file)
      }
      reload()
    } catch (err) {
      setUploadError(formatApiError(err, t, 'bannerRotation.errorUpload'))
    } finally {
      setter(false)
    }
  }

  const deleteImage = async (kind: 'banner' | 'icon', id: string) => {
    try {
      await deleteBannerRotationImage(kind, id)
      reload()
    } catch (err) {
      setError(formatApiError(err, t, 'bannerRotation.errorDelete'))
    }
  }

  const rotateNow = async () => {
    setRotating(true)
    setError('')
    setSaved('')
    try {
      const result = await triggerBannerRotation()
      if (result.settings) {
        setSettings({
          ...result.settings,
          banner_mode: result.settings.banner_mode === 'dynamic' ? 'dynamic' : 'playlist',
        })
      }
      setSaved(t('bannerRotation.rotatedOk'))
    } catch (err) {
      const code = err instanceof ApiError ? err.message : ''
      const fallback =
        code === 'nothing_to_rotate'
          ? 'bannerRotation.errorEmpty'
          : code === 'boost_required'
            ? 'bannerRotation.errorBoost'
            : code === 'invalid_image'
              ? 'bannerRotation.errorInvalidImage'
              : code === 'rate_limited'
                ? 'bannerRotation.errorRateLimited'
                : 'bannerRotation.errorRotate'
      let message = formatApiError(err, t, fallback)
      if (err instanceof ApiError) {
        const discordText = typeof err.body.discord_text === 'string' ? err.body.discord_text.trim() : ''
        const discordStatus = err.body.discord_status
        const discordCode = err.body.discord_code
        if (discordText) {
          const meta = [discordStatus != null ? `HTTP ${discordStatus}` : '', discordCode != null ? `code ${discordCode}` : '']
            .filter(Boolean)
            .join(', ')
          message = meta ? `${message} — Discord: ${discordText} (${meta})` : `${message} — Discord: ${discordText}`
        }
      }
      setError(message)
    } finally {
      setRotating(false)
    }
  }

  const patch = (partial: Partial<BannerRotationSettings>) =>
    setSettings((prev) => (prev ? { ...prev, ...partial } : prev))

  return (
    <div className="flex max-w-4xl flex-col gap-5 pb-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Image size={22} className="text-primary" />
          {t('bannerRotation.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => patch({ enabled: v })}
          label={settings.enabled ? t('bannerRotation.moduleOn') : t('bannerRotation.moduleOff')}
        />
        <Button
          variant="secondary"
          onClick={rotateNow}
          disabled={rotating || !settings.enabled}
          className="ml-auto"
        >
          {rotating ? t('bannerRotation.rotating') : t('bannerRotation.rotateNow')}
        </Button>
      </div>
      <p className="text-sm text-muted">{t('bannerRotation.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-4">
        <h2 className="font-semibold text-foreground">{t('bannerRotation.section.settings')}</h2>
        <Toggle
          checked={settings.banner_enabled}
          onChange={(v) => patch({ banner_enabled: v })}
          label={t('bannerRotation.bannerEnabled')}
        />
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">{t('bannerRotation.bannerMode')}</span>
          <Select
            id="br-banner-mode"
            value={settings.banner_mode}
          onChange={(id) => patch({ banner_mode: id === 'both' ? 'both' : id === 'dynamic' ? 'dynamic' : 'playlist' })}
            options={bannerModeOptions}
            placeholder={t('bannerRotation.bannerMode.playlist')}
            disabled={!settings.banner_enabled}
          />
          <span className="text-xs text-muted">{t('bannerRotation.bannerModeHint')}</span>
        </label>
        {dynamicMode && (
          <label className="flex flex-col gap-1 text-sm">
            <span className="text-muted">{t('bannerRotation.dynamicWindowDays')}</span>
            <input
              type="number"
              min={1}
              max={365}
              value={settings.dynamic_window_days}
              onChange={(e) => patch({ dynamic_window_days: Math.min(365, Math.max(1, Number(e.target.value) || 30)) })}
              className="w-40 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground"
            />
            <span className="text-xs text-muted">{t('bannerRotation.dynamicWindowDaysHint')}</span>
          </label>
        )}
        <Toggle
          checked={settings.icon_enabled}
          onChange={(v) => patch({ icon_enabled: v })}
          label={t('bannerRotation.iconEnabled')}
        />
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">{t('bannerRotation.interval')}</span>
          <input
            type="number"
            min={15}
            max={2880}
            value={settings.interval_minutes}
            onChange={(e) => patch({ interval_minutes: Number(e.target.value) || 60 })}
            className="w-40 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
          <span className="text-xs text-muted">{t('bannerRotation.intervalHint')}</span>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-muted">{t('bannerRotation.logChannel')}</span>
          <Select
            id="br-log-channel"
            value={settings.log_channel_id || ''}
            onChange={(id) => patch({ log_channel_id: id })}
            options={channelOptions}
            placeholder={t('bannerRotation.logChannelNone')}
          />
        </label>
        <div className="flex flex-col gap-1 text-xs text-muted">
          <span>
            {settings.last_banner_at
              ? t('bannerRotation.lastRotated', { date: formatTs(settings.last_banner_at, t) })
              : t('bannerRotation.neverRotated')}
          </span>
          {settings.next_run_at > 0 && (
            <span>
              {t('bannerRotation.nextRotation', { date: formatTs(settings.next_run_at, t) })}
            </span>
          )}
        </div>
      </Card>

      {uploadError && <p className="text-sm text-danger">{uploadError}</p>}

      <Card className={`flex flex-col gap-4 ${dynamicMode ? 'opacity-70' : ''}`}>
        <h2 className="font-semibold text-foreground">{t('bannerRotation.section.banners')}</h2>
        {dynamicMode && (
          <p className="text-sm text-muted">{t('bannerRotation.playlistDisabledHint')}</p>
        )}
        <ImageGrid
          images={settings.banners}
          onDelete={(id) => deleteImage('banner', id)}
          t={t}
        />
        <UploadZone
          onFiles={(files) => uploadImages('banner', files)}
          uploading={uploadingBanners}
          t={t}
          disabled={dynamicMode}
        />
      </Card>

      <Card className="flex flex-col gap-4">
        <h2 className="font-semibold text-foreground">{t('bannerRotation.section.icons')}</h2>
        <ImageGrid
          images={settings.icons}
          onDelete={(id) => deleteImage('icon', id)}
          t={t}
        />
        <UploadZone
          onFiles={(files) => uploadImages('icon', files)}
          uploading={uploadingIcons}
          t={t}
        />
      </Card>

      <div className="flex justify-end">
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
