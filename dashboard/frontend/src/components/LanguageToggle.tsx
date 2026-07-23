import { useLanguage, useT, type Lang } from '../context/LanguageContext'

export function LanguageToggle({ className = '' }: { className?: string }) {
  const { lang, setLang } = useLanguage()
  const t = useT()

  const toggle = (next: Lang) => {
    if (next !== lang) setLang(next)
  }

  return (
    <div
      className={`inline-flex rounded-control border border-border bg-surface p-0.5 text-xs font-medium ${className}`}
      role="group"
      aria-label={t('lang.switch')}
    >
      {(['ru', 'en'] as const).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => toggle(code)}
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
