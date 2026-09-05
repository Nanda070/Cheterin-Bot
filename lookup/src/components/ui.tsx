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
          className={`cursor-pointer rounded-[6px] px-2 py-1 transition-colors ${
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
    <Link to={to} className="flex items-center gap-2 font-semibold tracking-tight text-foreground">
      <span
        aria-hidden
        className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-sm font-bold text-white"
      >
        C
      </span>
      <span>{t('brand.name')}</span>
    </Link>
  )
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const t = useT()
  return (
    <div
      role="alert"
      className="rounded-[14px] border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-foreground"
    >
      <p>{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 cursor-pointer text-primary-hover underline-offset-2 hover:underline"
        >
          {t('common.retry')}
        </button>
      ) : null}
    </div>
  )
}

export function CopyButton({ value }: { value: string }) {
  const t = useT()
  const [copied, setCopied] = useState(false)

  return (
    <button
      type="button"
      className="cursor-pointer rounded-[8px] border border-border bg-surface px-2 py-1 text-xs text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
      onClick={() => {
        void copyText(value).then((ok) => {
          if (!ok) return
          setCopied(true)
          window.setTimeout(() => setCopied(false), 1500)
        })
      }}
    >
      {copied ? t('common.copied') : t('common.copy')}
    </button>
  )
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex rounded-full border border-border bg-surface px-2.5 py-0.5 text-xs text-muted">
      {children}
    </span>
  )
}

export function DetailRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-1 border-b border-border/70 py-2 sm:grid-cols-[140px_1fr] sm:gap-4">
      <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
      <dd className="break-all text-sm text-foreground">{children}</dd>
    </div>
  )
}
