import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { LanguageToggle } from '../components/LanguageToggle'
import { useT } from '../context/LanguageContext'

export type SecretRoomTheme = 'waterfall' | 'core' | 'judgment'

type Props = {
  theme: SecretRoomTheme
  /** i18n prefix, e.g. `room.waterfall` → title, name, line.0… */
  i18nPrefix: string
  lineCount: number
}

const THEME_CSS: Record<SecretRoomTheme, string> = {
  waterfall: `
    .sr-root {
      --fg: #c8e6ff;
      --accent: #5eb0ff;
      --box: #020810;
      min-height: 100dvh;
      background:
        radial-gradient(ellipse 80% 50% at 20% 100%, #0a2848 0%, transparent 55%),
        radial-gradient(ellipse 60% 40% at 90% 20%, #143050 0%, transparent 50%),
        linear-gradient(180deg, #02060e 0%, #040c18 50%, #010408 100%);
      color: var(--fg);
      font-family: 'Press Start 2P', ui-monospace, monospace;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      padding: 1.5rem 1rem 2rem;
      user-select: none;
    }
    .sr-mist {
      position: absolute; inset: 0; pointer-events: none;
      background: repeating-linear-gradient(
        90deg,
        transparent 0 11px,
        rgba(100,180,255,0.03) 11px 12px
      );
      animation: sr-drift 14s linear infinite;
    }
    @keyframes sr-drift {
      from { transform: translateX(0); }
      to { transform: translateX(-12px); }
    }
  `,
  core: `
    .sr-root {
      --fg: #e8fff4;
      --accent: #39ffb0;
      --box: #041008;
      min-height: 100dvh;
      background:
        linear-gradient(180deg, #030806 0%, #06140c 40%, #020504 100%);
      color: var(--fg);
      font-family: 'Press Start 2P', ui-monospace, monospace;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      padding: 1.5rem 1rem 2rem;
      user-select: none;
    }
    .sr-mist {
      position: absolute; inset: 0; pointer-events: none;
      background:
        linear-gradient(90deg, transparent 49%, rgba(57,255,176,0.08) 50%, transparent 51%),
        linear-gradient(0deg, transparent 49%, rgba(57,255,176,0.05) 50%, transparent 51%);
      background-size: 48px 48px;
      animation: sr-scan 3s steps(24) infinite;
      opacity: 0.5;
    }
    @keyframes sr-scan {
      from { background-position: 0 0; }
      to { background-position: 0 48px; }
    }
  `,
  judgment: `
    .sr-root {
      --fg: #fff6e8;
      --accent: #ffd56a;
      --box: #100806;
      min-height: 100dvh;
      background:
        radial-gradient(ellipse 70% 50% at 50% 0%, #3a2010 0%, transparent 60%),
        linear-gradient(180deg, #120a06 0%, #1a1008 45%, #0a0604 100%);
      color: var(--fg);
      font-family: 'Press Start 2P', ui-monospace, monospace;
      overflow: hidden;
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      padding: 1.5rem 1rem 2rem;
      user-select: none;
    }
    .sr-mist {
      position: absolute; inset: 0; pointer-events: none;
      box-shadow: inset 0 0 120px rgba(0,0,0,0.65);
    }
  `,
}

export function SecretRoomPage({ theme, i18nPrefix, lineCount }: Props) {
  const t = useT()
  const lines = useMemo(
    () => Array.from({ length: lineCount }, (_, i) => t(`${i18nPrefix}.line.${i}`)),
    [t, i18nPrefix, lineCount],
  )
  const [lineIndex, setLineIndex] = useState(0)
  const [visibleChars, setVisibleChars] = useState(0)

  useEffect(() => {
    const prev = document.title
    document.title = t(`${i18nPrefix}.title`)
    return () => {
      document.title = prev
    }
  }, [t, i18nPrefix])

  useEffect(() => {
    setLineIndex(0)
    setVisibleChars(0)
  }, [t])

  const line = lines[lineIndex] ?? ''
  const shown = line.slice(0, visibleChars)
  const typing = visibleChars < line.length

  useEffect(() => {
    if (!typing) return
    const id = window.setTimeout(() => setVisibleChars((c) => c + 1), theme === 'waterfall' ? 42 : 26)
    return () => window.clearTimeout(id)
  }, [typing, visibleChars, theme])

  const advance = useCallback(() => {
    if (typing) {
      setVisibleChars(line.length)
      return
    }
    setLineIndex((i) => (i + 1) % lines.length)
    setVisibleChars(0)
  }, [typing, line.length, lines.length])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        advance()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [advance])

  return (
    <div className="sr-root" onClick={advance} role="presentation">
      <style>{THEME_CSS[theme]}</style>
      <style>{`
        .sr-top {
          position: absolute; top: 0.75rem; left: 0; right: 0;
          display: flex; justify-content: space-between; align-items: center;
          padding: 0 1rem; z-index: 2; font-size: 0.55rem; gap: 0.75rem;
        }
        .sr-top a { color: var(--accent); text-decoration: none; }
        .sr-top a:hover { text-decoration: underline; }
        .sr-stage {
          position: relative; z-index: 1; width: min(36rem, 100%);
          flex: 1; display: flex; flex-direction: column; justify-content: flex-end;
          gap: 1.25rem;
        }
        .sr-figure {
          align-self: flex-start; margin-left: 1rem;
          font-size: 0.65rem; letter-spacing: 0.08em; color: var(--accent);
          text-shadow: 0 0 12px color-mix(in srgb, var(--accent) 50%, transparent);
        }
        .sr-box {
          border: 4px solid var(--fg);
          background: var(--box);
          min-height: 7.5rem;
          padding: 1rem 1.1rem 1.25rem;
          box-shadow: 0 0 0 2px var(--box), 0 0 40px rgba(0,0,0,0.45);
        }
        .sr-box .sr-name {
          color: var(--accent); font-size: 0.55rem; margin-bottom: 0.65rem;
        }
        .sr-box .sr-text {
          font-size: 0.62rem; line-height: 1.85; min-height: 3.6em; word-break: break-word;
        }
        .sr-cursor {
          display: inline-block; width: 0.55em; height: 0.85em;
          background: var(--fg); margin-left: 2px; vertical-align: -2px;
          animation: sr-blink 0.9s step-end infinite;
        }
        @keyframes sr-blink { 50% { opacity: 0; } }
        .sr-hint {
          text-align: center; font-size: 0.45rem; opacity: 0.45; margin-top: 0.75rem;
        }
      `}</style>
      <div className="sr-mist" aria-hidden />
      <div className="sr-top">
        <Link to="/" onClick={(e) => e.stopPropagation()}>
          {t(`${i18nPrefix}.back`)}
        </Link>
        <span onClick={(e) => e.stopPropagation()}>
          <LanguageToggle />
        </span>
      </div>
      <div className="sr-stage">
        <div className="sr-figure" aria-hidden>
          {t(`${i18nPrefix}.figure`)}
        </div>
        <div
          className="sr-box"
          role="dialog"
          aria-label={t(`${i18nPrefix}.dialogueAria`)}
        >
          <div className="sr-name">{t(`${i18nPrefix}.name`)}</div>
          <div className="sr-text">
            {shown}
            {typing ? <span className="sr-cursor" aria-hidden /> : null}
          </div>
          <p className="sr-hint">{t(`${i18nPrefix}.hint`)}</p>
        </div>
      </div>
    </div>
  )
}

export function WaterfallRoomPage() {
  return <SecretRoomPage theme="waterfall" i18nPrefix="room.waterfall" lineCount={8} />
}

export function CoreRoomPage() {
  return <SecretRoomPage theme="core" i18nPrefix="room.core" lineCount={8} />
}

export function JudgmentRoomPage() {
  return <SecretRoomPage theme="judgment" i18nPrefix="room.judgment" lineCount={9} />
}
