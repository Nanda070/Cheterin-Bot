import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useLanguage, useT } from '../context/LanguageContext'
import { copyText } from '../lib/discord'

export function LanguageToggle({ className = '' }: { className?: string }) {
  const { lang, setLang } = useLanguage()
  const t = useT()

  return (
    <div
      className={`inline-flex rounded-[10px] border border-border bg-surface p-0.5 text-xs font-medium ${className}`}
      role="group"
      aria-label={t('lang.switch')}
    >
      {(['ru', 'en'] as const).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => {
            if (code !== lang) setLang(code)
          }}
          className={`cursor-pointer rounded-[6px] px-2.5 py-1 transition-colors ${
            lang === code ? 'bg-primary-muted text-foreground' : 'text-muted hover:text-foreground'
          }`}
          aria-label={t(`lang.${code}`)}
          aria-pressed={lang === code}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  )
}

export function BrandMark({ to = '/' }: { to?: string }) {
  const t = useT()
  return (
    <Link to={to} className="group flex items-center gap-2.5 font-display text-[1.05rem] font-semibold tracking-tight text-foreground">
      <span
        aria-hidden
        className="inline-flex h-8 w-8 items-center justify-center rounded-[10px] bg-primary text-sm font-bold text-white transition-transform duration-200 group-hover:scale-[1.03]"
      >
        C
      </span>
      <span>{t('brand.name')}</span>
    </Link>
  )
}

export function PageHeader({
  title,
  lead,
  eyebrow,
  actions,
}: {
  title: string
  lead?: string
  eyebrow?: string
  actions?: ReactNode
}) {
  return (
    <header className="lookup-rise flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? (
          <p className="mb-2 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-primary-hover">{eyebrow}</p>
        ) : null}
        <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
        {lead ? <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted sm:text-base">{lead}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
    </header>
  )
}

export function Panel({
  children,
  className = '',
  raised = false,
}: {
  children: ReactNode
  className?: string
  raised?: boolean
}) {
  return <div className={`${raised ? 'lookup-panel-raised' : 'lookup-panel'} ${className}`}>{children}</div>
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="font-display text-lg font-semibold tracking-tight">{children}</h2>
      {action}
    </div>
  )
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const t = useT()
  return (
    <div
      role="alert"
      className="rounded-[14px] border border-danger/35 bg-danger/10 px-4 py-3.5 text-sm text-foreground"
    >
      <p className="leading-relaxed">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 inline-flex cursor-pointer rounded-[10px] border border-border bg-surface px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:border-primary/40 hover:bg-surface-hover"
        >
          {t('common.retry')}
        </button>
      ) : null}
    </div>
  )
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <Panel className="px-5 py-8 text-center sm:px-8">
      <p className="font-display text-base font-semibold">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-muted">{body}</p>
    </Panel>
  )
}

export function LoadingBlock({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-busy="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="lookup-skeleton h-12 rounded-[12px]"
          style={{ opacity: 1 - i * 0.12 }}
        />
      ))}
    </div>
  )
}

export function CopyButton({ value, label }: { value: string; label?: string }) {
  const t = useT()
  const [copied, setCopied] = useState(false)

  return (
    <button
      type="button"
      className="cursor-pointer rounded-[8px] border border-border bg-surface px-2.5 py-1 text-xs font-medium text-muted transition-colors hover:border-border-strong hover:bg-surface-hover hover:text-foreground"
      onClick={() => {
        void copyText(value).then((ok) => {
          if (!ok) return
          setCopied(true)
          window.setTimeout(() => setCopied(false), 1500)
        })
      }}
    >
      {copied ? t('common.copied') : label || t('common.copy')}
    </button>
  )
}

export function Tag({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'accent' }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[0.7rem] font-medium tracking-wide ${
        tone === 'accent'
          ? 'border-primary/35 bg-primary-muted text-primary-hover'
          : 'border-border bg-background-deep text-muted'
      }`}
    >
      {children}
    </span>
  )
}

export function DetailRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-border/60 py-2.5 last:border-b-0 sm:grid-cols-[minmax(110px,38%)_1fr] sm:gap-4">
      <dt className="text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-muted">{label}</dt>
      <dd className="break-all text-sm leading-relaxed text-foreground">{children}</dd>
    </div>
  )
}

export function DetailGrid({ children }: { children: ReactNode }) {
  return <div className="grid gap-x-8 gap-y-0 lg:grid-cols-2">{children}</div>
}

export function GhostLink({
  to,
  href,
  children,
}: {
  to?: string
  href?: string
  children: ReactNode
}) {
  const className =
    'inline-flex cursor-pointer items-center rounded-[8px] border border-border bg-surface px-2.5 py-1 text-xs font-medium text-muted transition-colors hover:border-border-strong hover:bg-surface-hover hover:text-foreground'
  if (to) {
    return (
      <Link to={to} className={className}>
        {children}
      </Link>
    )
  }
  return (
    <a href={href} className={className} target={href?.startsWith('http') ? '_blank' : undefined} rel="noreferrer">
      {children}
    </a>
  )
}

export function PrimaryButton({
  children,
  type = 'button',
  className = '',
  onClick,
}: {
  children: ReactNode
  type?: 'button' | 'submit'
  className?: string
  onClick?: () => void
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`cursor-pointer rounded-[12px] bg-primary px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover ${className}`}
    >
      {children}
    </button>
  )
}

export function Field({
  id,
  label,
  hint,
  children,
  className = '',
}: {
  id?: string
  label: string
  hint?: string
  children: ReactNode
  className?: string
}) {
  return (
    <label className={`block text-sm ${className}`} htmlFor={id}>
      <span className="text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-muted">{label}</span>
      <div className="mt-1.5">{children}</div>
      {hint ? <p className="mt-1.5 text-xs text-muted">{hint}</p> : null}
    </label>
  )
}

export const controlClass =
  'w-full rounded-[10px] border border-border bg-background-deep px-3 py-2.5 text-sm text-foreground outline-none transition-[border-color,box-shadow] placeholder:text-muted focus:border-primary/60'

export function ProfileBanner({
  imageUrl,
  accent,
}: {
  imageUrl?: string | null
  accent?: string | null
}) {
  return (
    <div
      className="relative h-40 overflow-hidden bg-primary-deep sm:h-48"
      style={
        imageUrl
          ? { backgroundImage: `url(${imageUrl})`, backgroundSize: 'cover', backgroundPosition: 'center' }
          : accent
            ? { backgroundColor: accent }
            : undefined
      }
    >
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-surface via-transparent to-black/20" />
    </div>
  )
}
