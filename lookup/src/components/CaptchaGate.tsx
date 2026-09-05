/**
 * CaptchaGate — shown when the API returns captcha_required (429 rate limit threshold).
 *
 * If the operator has configured LOOKUP_CAPTCHA_ENABLED=true + LOOKUP_CAPTCHA_SITE_KEY,
 * the appropriate widget (Turnstile or hCaptcha) is loaded and rendered.
 * After a successful solve, the backend clears the IP gate and `onVerified` is called.
 *
 * If CAPTCHA is not configured, a simple "wait and retry" message is shown instead.
 *
 * Operator setup (in lookup-api/.env):
 *   LOOKUP_CAPTCHA_ENABLED=true
 *   LOOKUP_CAPTCHA_PROVIDER=turnstile   # or hcaptcha
 *   LOOKUP_CAPTCHA_SITE_KEY=<your-public-site-key>
 *   LOOKUP_CAPTCHA_SECRET=<your-private-secret>
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { verifyCaptcha, type LookupConfig } from '../api/client'
import { useT } from '../context/LanguageContext'

// Extend window for CAPTCHA globals
declare global {
  interface Window {
    turnstile?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => string
      remove: (widgetId: string) => void
      reset: (widgetId: string) => void
    }
    hcaptcha?: {
      render: (container: string | HTMLElement, options: Record<string, unknown>) => string
      remove: (widgetId: string) => void
      reset: (widgetId: string) => void
    }
    onCaptchaSolved?: (token: string) => void
  }
}

type Props = {
  config: LookupConfig | null
  onVerified: () => void
  onDismiss?: () => void
}

const PROVIDER_SCRIPTS: Record<string, string> = {
  turnstile: 'https://challenges.cloudflare.com/turnstile/v0/api.js',
  hcaptcha: 'https://js.hcaptcha.com/1/api.js',
}

/** Inject the CAPTCHA provider script once and call back when ready. */
function loadScript(src: string, onLoad: () => void): void {
  if (document.querySelector(`script[src="${src}"]`)) {
    onLoad()
    return
  }
  const script = document.createElement('script')
  script.src = src
  script.async = true
  script.defer = true
  script.onload = onLoad
  document.head.appendChild(script)
}

export function CaptchaGate({ config, onVerified, onDismiss }: Props) {
  const t = useT()
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string | null>(null)
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'verifying' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const captchaEnabled = config?.captcha_enabled && config.captcha_site_key && config.captcha_provider
  const provider = config?.captcha_provider ?? 'turnstile'
  const siteKey = config?.captcha_site_key ?? ''

  const handleToken = useCallback(
    async (token: string) => {
      setStatus('verifying')
      try {
        await verifyCaptcha(token)
        onVerified()
      } catch {
        setStatus('error')
        setErrorMsg(t('captcha.error'))
        // Reset widget on failure
        if (widgetIdRef.current !== null) {
          try {
            if (provider === 'turnstile') window.turnstile?.reset(widgetIdRef.current)
            else window.hcaptcha?.reset(widgetIdRef.current)
          } catch {
            /* ignore */
          }
        }
      }
    },
    [onVerified, provider, t],
  )

  useEffect(() => {
    if (!captchaEnabled || !containerRef.current) return

    const scriptSrc = PROVIDER_SCRIPTS[provider]
    if (!scriptSrc) return

    setStatus('loading')

    const renderWidget = () => {
      if (!containerRef.current) return
      try {
        const api = provider === 'turnstile' ? window.turnstile : window.hcaptcha
        if (!api) return
        widgetIdRef.current = api.render(containerRef.current, {
          sitekey: siteKey,
          callback: handleToken,
          theme: 'dark',
          size: 'normal',
        })
        setStatus('ready')
      } catch {
        setStatus('error')
        setErrorMsg(t('captcha.error'))
      }
    }

    loadScript(scriptSrc, renderWidget)

    return () => {
      if (widgetIdRef.current !== null) {
        try {
          if (provider === 'turnstile') window.turnstile?.remove(widgetIdRef.current)
          else window.hcaptcha?.remove(widgetIdRef.current)
        } catch {
          /* ignore */
        }
        widgetIdRef.current = null
      }
    }
  }, [captchaEnabled, provider, siteKey, handleToken, t])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="captcha-title"
    >
      <div className="w-full max-w-sm rounded-[16px] border border-border bg-surface p-6 shadow-[0_24px_60px_-28px_rgb(0_0_0_/_0.85)]">
        <h2 id="captcha-title" className="font-display text-lg font-semibold">
          {t('captcha.title')}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          {captchaEnabled ? t('captcha.instructions') : t('captcha.noProvider')}
        </p>

        {captchaEnabled && (
          <div className="mt-5">
            {status === 'error' && (
              <p role="alert" className="mb-3 text-sm text-danger">
                {errorMsg}
              </p>
            )}
            {status === 'verifying' ? (
              <p className="text-sm text-muted">{t('captcha.verifying')}</p>
            ) : (
              <div ref={containerRef} className="min-h-[65px]" />
            )}
          </div>
        )}

        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="mt-5 w-full cursor-pointer rounded-[10px] border border-border bg-surface-hover px-4 py-2 text-sm text-muted transition-colors hover:text-foreground"
          >
            {t('common.back')}
          </button>
        )}
      </div>
    </div>
  )
}
