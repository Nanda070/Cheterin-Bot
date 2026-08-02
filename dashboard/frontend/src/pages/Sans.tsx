import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LanguageToggle } from '../components/LanguageToggle'
import { useT } from '../context/LanguageContext'

/**
 * Secret Undertale homage.
 *
 * Music: optional user-supplied file at `/sans-music.mp3` or `/sans-music.ogg`
 * in `dashboard/frontend/public/` (not shipped — place your own legally obtained
 * track; Snowdin Town fits best). Playback starts on the music toggle click.
 * Missing files must not be detected via bare HTTP 200 — Vite SPA fallback
 * serves index.html for unknown paths. If no playable file, falls back to an
 * original Web Audio cozy loop (not the OST).
 */

const SANS_LINE_COUNT = 11
// Prefer mp3 first — users commonly drop `public/sans-music.mp3`. Ogg still probed.
// Do NOT trust bare 200 from HEAD/GET: Vite SPA fallback returns index.html for missing files.
const LOCAL_MUSIC_CANDIDATES = ['/sans-music.mp3', '/sans-music.ogg'] as const

const STARS = Array.from({ length: 48 }, (_, i) => ({
  id: i,
  left: `${(i * 37) % 100}%`,
  top: `${(i * 53) % 70}%`,
  delay: `${(i % 12) * 0.35}s`,
  size: 1 + (i % 3),
}))

const SNOW = Array.from({ length: 36 }, (_, i) => ({
  id: i,
  left: `${(i * 29) % 100}%`,
  delay: `${(i % 18) * 0.4}s`,
  duration: `${8 + (i % 7)}s`,
  size: 2 + (i % 4),
}))

type AudioKit = {
  setVolume: (v: number) => void
  stop: () => void
  resume: () => Promise<void>
}

function armGestureResume(play: () => Promise<void>): () => void {
  let armed = true
  const unlock = () => {
    if (!armed) return
    armed = false
    window.removeEventListener('pointerdown', unlock)
    window.removeEventListener('keydown', unlock)
    void play()
  }
  window.addEventListener('pointerdown', unlock)
  window.addEventListener('keydown', unlock)
  return () => {
    armed = false
    window.removeEventListener('pointerdown', unlock)
    window.removeEventListener('keydown', unlock)
  }
}

function wrapFileAudio(audio: HTMLAudioElement): AudioKit {
  let disarmGesture: (() => void) | null = null

  const tryPlay = async () => {
    await audio.play()
    disarmGesture?.()
    disarmGesture = null
  }

  return {
    setVolume: (v) => {
      audio.volume = Math.min(1, Math.max(0, v))
    },
    stop: () => {
      disarmGesture?.()
      disarmGesture = null
      audio.pause()
      audio.removeAttribute('src')
      audio.load()
    },
    resume: async () => {
      try {
        await tryPlay()
      } catch {
        // Autoplay blocked — unlock on the next click/key.
        disarmGesture?.()
        disarmGesture = armGestureResume(tryPlay)
      }
    },
  }
}

/** Begin looping a local file. Call audio.play() during a user gesture when possible. */
function beginFileAudio(url: string, volume: number): { kit: AudioKit; playPromise: Promise<void> } {
  const audio = new Audio(url)
  audio.loop = true
  audio.preload = 'auto'
  audio.volume = Math.min(1, Math.max(0, volume))
  // Invoke play() synchronously so the call stack still has user activation.
  const playPromise = audio.play().then(() => undefined)
  return { kit: wrapFileAudio(audio), playPromise }
}

function startCozyLoop(volume: number): AudioKit {
  const ctx = new AudioContext()
  const master = ctx.createGain()
  master.gain.value = volume
  master.connect(ctx.destination)
  let disarmGesture: (() => void) | null = null

  // Soft low pad
  const pad = ctx.createOscillator()
  pad.type = 'sine'
  pad.frequency.value = 110
  const padGain = ctx.createGain()
  padGain.gain.value = 0.045
  pad.connect(padGain)
  padGain.connect(master)
  pad.start()

  // Gentle pentatonic lullaby (original) — Snowdin-adjacent mood, not OST.
  const melody = [196.0, 220.0, 261.63, 293.66, 329.63, 293.66, 261.63, 220.0]
  const tempo = 0.55
  let step = 0
  let cancelled = false
  const timers: number[] = []

  const tick = () => {
    if (cancelled || ctx.state === 'closed') return
    try {
      const now = ctx.currentTime
      const freq = melody[step % melody.length]
      const osc = ctx.createOscillator()
      osc.type = 'triangle'
      osc.frequency.value = freq
      const g = ctx.createGain()
      g.gain.setValueAtTime(0.0001, now)
      g.gain.exponentialRampToValueAtTime(0.07, now + 0.04)
      g.gain.exponentialRampToValueAtTime(0.0001, now + tempo * 0.95)
      const filter = ctx.createBiquadFilter()
      filter.type = 'lowpass'
      filter.frequency.value = 1200
      osc.connect(filter)
      filter.connect(g)
      g.connect(master)
      osc.start(now)
      osc.stop(now + tempo)
      step += 1
      timers.push(window.setTimeout(tick, tempo * 1000) as unknown as number)
    } catch {
      cancelled = true
    }
  }
  tick()

  const tryResume = async () => {
    if (ctx.state === 'suspended') await ctx.resume()
    disarmGesture?.()
    disarmGesture = null
  }

  return {
    setVolume: (v) => {
      master.gain.value = v
    },
    stop: () => {
      cancelled = true
      disarmGesture?.()
      disarmGesture = null
      timers.forEach((id) => window.clearTimeout(id))
      try {
        pad.stop()
      } catch {
        /* already stopped */
      }
      void ctx.close()
    },
    resume: async () => {
      try {
        await tryResume()
      } catch {
        disarmGesture?.()
        disarmGesture = armGestureResume(tryResume)
      }
    },
  }
}

/**
 * Start music. Prefer calling from a click handler so play() keeps user
 * activation. All candidate play() calls are kicked off synchronously (before
 * any await); SPA HTML fallbacks fail decode and are skipped. Falls back to an
 * original Web Audio loop when no file is playable.
 */
async function startSansMusic(volume: number): Promise<AudioKit> {
  // Start every candidate under the same user gesture, then keep the first that plays.
  const attempts = LOCAL_MUSIC_CANDIDATES.map((url) => beginFileAudio(url, volume))
  for (const { kit, playPromise } of attempts) {
    try {
      await playPromise
      for (const other of attempts) {
        if (other.kit !== kit) other.kit.stop()
      }
      return kit
    } catch {
      kit.stop()
    }
  }
  const cozy = startCozyLoop(volume)
  await cozy.resume()
  return cozy
}

export function SansPage() {
  const t = useT()
  const lines = useMemo(
    () => Array.from({ length: SANS_LINE_COUNT }, (_, i) => t(`sans.line.${i}`)),
    [t],
  )
  const [lineIndex, setLineIndex] = useState(0)
  const [visibleChars, setVisibleChars] = useState(0)
  const [musicOn, setMusicOn] = useState(false)
  const [sfxOn, setSfxOn] = useState(true)
  const [volume, setVolume] = useState(0.35)
  const [wink, setWink] = useState(false)
  const kitRef = useRef<AudioKit | null>(null)
  const blipRef = useRef<AudioContext | null>(null)
  const volumeRef = useRef(volume)
  const musicGenRef = useRef(0)
  volumeRef.current = volume

  useEffect(() => {
    const prev = document.title
    document.title = '…'
    return () => {
      document.title = prev
    }
  }, [])

  useEffect(() => {
    setLineIndex(0)
    setVisibleChars(0)
  }, [t])

  const line = lines[lineIndex] ?? ''
  const shown = line.slice(0, visibleChars)
  const typing = visibleChars < line.length

  const playBlip = useCallback(() => {
    if (!sfxOn || volume <= 0) return
    try {
      if (!blipRef.current || blipRef.current.state === 'closed') {
        blipRef.current = new AudioContext()
      }
      const ctx = blipRef.current
      if (ctx.state === 'suspended') void ctx.resume()
      const now = ctx.currentTime
      const osc = ctx.createOscillator()
      const g = ctx.createGain()
      osc.type = 'square'
      osc.frequency.value = 520 + Math.random() * 80
      const peak = Math.max(0.0001, 0.04 * volume)
      g.gain.setValueAtTime(peak, now)
      g.gain.exponentialRampToValueAtTime(0.0001, now + 0.05)
      osc.connect(g)
      g.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + 0.06)
    } catch {
      /* autoplay / unsupported */
    }
  }, [sfxOn, volume])

  useEffect(() => {
    if (!typing) return
    const id = window.setTimeout(() => {
      setVisibleChars((c) => c + 1)
      playBlip()
    }, 28)
    return () => window.clearTimeout(id)
  }, [typing, visibleChars, playBlip])

  useEffect(() => {
    const id = window.setInterval(() => setWink((w) => !w), 3200)
    return () => window.clearInterval(id)
  }, [])

  // Stop when toggled off; start happens in toggleMusic (needs user gesture).
  useEffect(() => {
    if (musicOn) return
    musicGenRef.current += 1
    kitRef.current?.stop()
    kitRef.current = null
  }, [musicOn])

  useEffect(() => {
    kitRef.current?.setVolume(volume)
  }, [volume])

  useEffect(() => {
    return () => {
      musicGenRef.current += 1
      kitRef.current?.stop()
      kitRef.current = null
      void blipRef.current?.close()
    }
  }, [])

  const advance = () => {
    if (typing) {
      setVisibleChars(line.length)
      return
    }
    setLineIndex((i) => (i + 1) % lines.length)
    setVisibleChars(0)
  }

  const toggleMusic = () => {
    if (musicOn) {
      setMusicOn(false)
      return
    }
    setMusicOn(true)
    const gen = ++musicGenRef.current
    const vol = volumeRef.current
    // startSansMusic calls audio.play() synchronously before any await,
    // while this click still counts as user activation.
    void (async () => {
      try {
        const kit = await startSansMusic(vol)
        if (gen !== musicGenRef.current) {
          kit.stop()
          return
        }
        kitRef.current?.stop()
        kitRef.current = kit
        kit.setVolume(volumeRef.current)
      } catch {
        if (gen !== musicGenRef.current) return
        const kit = startCozyLoop(vol)
        kitRef.current?.stop()
        kitRef.current = kit
        await kit.resume()
        kit.setVolume(volumeRef.current)
      }
    })()
  }

  return (
    <div className="sans-root">
      <style>{`
        .sans-root {
          --snow: #e8f4ff;
          --night: #0a0e18;
          --pine: #1a2a3a;
          --glow: #7ec8ff;
          --gold: #ffe56d;
          --box: #000;
          min-height: 100dvh;
          background:
            radial-gradient(ellipse 120% 80% at 50% -10%, #1a2740 0%, transparent 55%),
            radial-gradient(ellipse 60% 40% at 80% 90%, #152030 0%, transparent 50%),
            linear-gradient(180deg, #0c1220 0%, #080b12 45%, #05070c 100%);
          color: var(--snow);
          font-family: 'Press Start 2P', ui-monospace, monospace;
          overflow: hidden;
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-end;
          padding: 1.5rem 1rem 2rem;
          cursor: default;
          user-select: none;
        }

        .sans-stars span {
          position: absolute;
          background: #cfe8ff;
          border-radius: 50%;
          opacity: 0.35;
          animation: sans-twinkle 3.5s ease-in-out infinite;
          pointer-events: none;
        }

        @keyframes sans-twinkle {
          0%, 100% { opacity: 0.2; transform: scale(1); }
          50% { opacity: 0.85; transform: scale(1.4); }
        }

        .sans-snowflake {
          position: absolute;
          top: -8px;
          background: #fff;
          border-radius: 50%;
          opacity: 0.55;
          animation-name: sans-fall;
          animation-timing-function: linear;
          animation-iteration-count: infinite;
          pointer-events: none;
          box-shadow: 0 0 4px rgba(200, 230, 255, 0.6);
        }

        @keyframes sans-fall {
          0% { transform: translateY(-5vh) translateX(0); opacity: 0; }
          10% { opacity: 0.7; }
          100% { transform: translateY(105vh) translateX(24px); opacity: 0.15; }
        }

        .sans-horizon {
          position: absolute;
          inset: auto 0 28% 0;
          height: 42%;
          background:
            linear-gradient(180deg, transparent 0%, rgba(20, 36, 56, 0.55) 40%, rgba(12, 20, 32, 0.9) 100%);
          pointer-events: none;
        }

        .sans-trees {
          position: absolute;
          bottom: 26%;
          left: 0;
          right: 0;
          height: 18%;
          background:
            repeating-linear-gradient(
              90deg,
              transparent 0 28px,
              rgba(30, 50, 70, 0.55) 28px 36px,
              transparent 36px 70px
            );
          mask-image: linear-gradient(180deg, transparent, #000 30%, #000 80%, transparent);
          pointer-events: none;
          opacity: 0.7;
        }

        .sans-stage {
          position: relative;
          z-index: 2;
          width: min(560px, 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1.25rem;
        }

        .sans-face {
          width: 120px;
          height: 100px;
          position: relative;
          filter: drop-shadow(0 0 18px rgba(126, 200, 255, 0.35));
          animation: sans-breathe 4s ease-in-out infinite;
        }

        @keyframes sans-breathe {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }

        .sans-skull {
          width: 100%;
          height: 78px;
          background: #f2f6fa;
          border-radius: 48% 48% 42% 42%;
          position: relative;
          border: 3px solid #1a1a1a;
          box-shadow: inset 0 -8px 0 rgba(0,0,0,0.06);
        }

        .sans-eye {
          position: absolute;
          top: 28px;
          width: 18px;
          height: 22px;
          background: #111;
          border-radius: 40%;
        }
        .sans-eye.left { left: 28px; }
        .sans-eye.right { right: 28px; }
        .sans-eye.wink {
          height: 3px;
          top: 38px;
          border-radius: 2px;
          background: #222;
        }
        .sans-pupil {
          position: absolute;
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--glow);
          box-shadow: 0 0 8px var(--glow), 0 0 16px rgba(126, 200, 255, 0.7);
          top: 7px;
          left: 5px;
        }
        .sans-nose {
          position: absolute;
          top: 48px;
          left: 50%;
          width: 10px;
          height: 8px;
          margin-left: -5px;
          background: #111;
          clip-path: polygon(50% 100%, 0 0, 100% 0);
        }
        .sans-smile {
          position: absolute;
          bottom: 12px;
          left: 50%;
          width: 42px;
          height: 14px;
          margin-left: -21px;
          border: 3px solid #111;
          border-top: none;
          border-radius: 0 0 24px 24px;
        }
        .sans-hoodie {
          width: 92px;
          height: 28px;
          margin: -4px auto 0;
          background: #2a4a78;
          border-radius: 0 0 10px 10px;
          border: 3px solid #1a1a1a;
          border-top: none;
          position: relative;
        }
        .sans-hoodie::before {
          content: '';
          position: absolute;
          top: -6px;
          left: -8px;
          right: -8px;
          height: 12px;
          background: #345a8c;
          border-radius: 8px 8px 0 0;
          border: 3px solid #1a1a1a;
          border-bottom: none;
        }

        .sans-z {
          position: absolute;
          top: -8px;
          right: -18px;
          color: var(--glow);
          font-size: 10px;
          opacity: 0;
          animation: sans-z 2.4s ease-in-out infinite;
        }
        .sans-z.on { opacity: 1; }

        @keyframes sans-z {
          0% { transform: translate(0, 0) scale(0.8); opacity: 0; }
          30% { opacity: 0.9; }
          100% { transform: translate(14px, -22px) scale(1.2); opacity: 0; }
        }

        .sans-box {
          width: 100%;
          background: #000;
          border: 4px solid #fff;
          box-shadow:
            0 0 0 2px #000,
            0 12px 40px rgba(0, 0, 0, 0.55),
            0 0 28px rgba(126, 200, 255, 0.12);
          padding: 1.1rem 1.15rem 1.35rem;
          min-height: 7.5rem;
          position: relative;
          cursor: pointer;
        }

        .sans-box:focus-visible {
          outline: 2px solid var(--gold);
          outline-offset: 3px;
        }

        .sans-name {
          color: var(--gold);
          font-size: 10px;
          letter-spacing: 0.08em;
          margin-bottom: 0.85rem;
          text-shadow: 0 0 12px rgba(255, 229, 109, 0.35);
        }

        .sans-text {
          font-size: clamp(10px, 2.6vw, 12px);
          line-height: 1.85;
          color: #fff;
          min-height: 3.6em;
          white-space: pre-wrap;
        }

        .sans-caret {
          display: inline-block;
          width: 10px;
          height: 12px;
          background: #fff;
          margin-left: 2px;
          vertical-align: -1px;
          animation: sans-blink 0.9s step-end infinite;
        }

        @keyframes sans-blink {
          50% { opacity: 0; }
        }

        .sans-hint {
          position: absolute;
          right: 12px;
          bottom: 8px;
          font-size: 8px;
          color: #888;
          letter-spacing: 0.06em;
        }

        .sans-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 0.55rem;
          justify-content: center;
          width: 100%;
        }

        .sans-btn {
          font-family: inherit;
          font-size: 8px;
          letter-spacing: 0.04em;
          padding: 0.65rem 0.85rem;
          background: rgba(8, 12, 20, 0.85);
          color: var(--snow);
          border: 2px solid #4a6a88;
          cursor: pointer;
          transition: border-color 0.15s, background 0.15s, color 0.15s;
        }
        .sans-btn:hover {
          border-color: var(--glow);
          color: #fff;
          background: rgba(20, 36, 56, 0.95);
        }
        .sans-btn.active {
          border-color: var(--gold);
          color: var(--gold);
          box-shadow: 0 0 14px rgba(255, 229, 109, 0.2);
        }

        .sans-vol {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 8px;
          color: #9bb4cc;
          padding: 0.35rem 0.5rem;
        }
        .sans-vol input {
          width: 88px;
          accent-color: var(--glow);
        }

        .sans-footer {
          margin-top: 0.75rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.55rem;
          text-align: center;
        }
        .sans-credit {
          font-size: 7px;
          color: #6a8299;
          line-height: 1.7;
          max-width: 36rem;
        }
        .sans-home {
          font-size: 8px;
          color: #8aa4bc;
          text-decoration: none;
          border-bottom: 1px dotted #4a6a88;
          padding-bottom: 2px;
        }
        .sans-home:hover { color: var(--glow); border-color: var(--glow); }

        .sans-title {
          position: absolute;
          top: 1.4rem;
          left: 50%;
          transform: translateX(-50%);
          z-index: 3;
          font-size: clamp(9px, 2.4vw, 11px);
          letter-spacing: 0.28em;
          color: rgba(200, 230, 255, 0.55);
          text-transform: uppercase;
        }

        .sans-lang {
          position: absolute;
          top: 1rem;
          right: 1rem;
          z-index: 4;
        }
        .sans-lang > div {
          border-color: #4a6a88 !important;
          background: rgba(8, 12, 20, 0.85) !important;
          font-family: 'Press Start 2P', ui-monospace, monospace;
          font-size: 8px;
        }
        .sans-lang button {
          color: #9bb4cc !important;
        }
        .sans-lang button[aria-pressed='true'] {
          background: rgba(126, 200, 255, 0.18) !important;
          color: #e8f4ff !important;
        }
      `}</style>

      <div className="sans-lang">
        <LanguageToggle />
      </div>

      <div className="sans-stars" aria-hidden>
        {STARS.map((s) => (
          <span
            key={s.id}
            style={{
              left: s.left,
              top: s.top,
              width: s.size,
              height: s.size,
              animationDelay: s.delay,
            }}
          />
        ))}
      </div>

      {SNOW.map((f) => (
        <span
          key={f.id}
          className="sans-snowflake"
          aria-hidden
          style={{
            left: f.left,
            width: f.size,
            height: f.size,
            animationDelay: f.delay,
            animationDuration: f.duration,
          }}
        />
      ))}

      <div className="sans-horizon" aria-hidden />
      <div className="sans-trees" aria-hidden />

      <p className="sans-title">{t('sans.title')}</p>

      <div className="sans-stage">
        <div className="sans-face" aria-hidden>
          <span className={`sans-z ${musicOn ? 'on' : ''}`}>z</span>
          <div className="sans-skull">
            <div className={`sans-eye left ${wink ? 'wink' : ''}`}>
              {!wink && <span className="sans-pupil" />}
            </div>
            <div className="sans-eye right">
              <span className="sans-pupil" />
            </div>
            <div className="sans-nose" />
            <div className="sans-smile" />
          </div>
          <div className="sans-hoodie" />
        </div>

        <div
          className="sans-box"
          role="button"
          tabIndex={0}
          onClick={advance}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowRight') {
              e.preventDefault()
              advance()
            }
          }}
          aria-label={t('sans.dialogueAria')}
        >
          <div className="sans-name">{t('sans.name')}</div>
          <p className="sans-text">
            {shown}
            {typing && <span className="sans-caret" aria-hidden />}
          </p>
          {!typing && <span className="sans-hint">▼</span>}
        </div>

        <div className="sans-controls">
          <button
            type="button"
            className={`sans-btn ${musicOn ? 'active' : ''}`}
            onClick={() => void toggleMusic()}
            aria-pressed={musicOn}
          >
            {musicOn ? t('sans.musicOn') : t('sans.musicOff')}
          </button>
          <button
            type="button"
            className={`sans-btn ${sfxOn ? 'active' : ''}`}
            onClick={() => setSfxOn((v) => !v)}
            aria-pressed={sfxOn}
          >
            {sfxOn ? t('sans.sfxOn') : t('sans.sfxOff')}
          </button>
          <label className="sans-vol">
            {t('sans.vol')}
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={(e) => setVolume(Number(e.target.value))}
              aria-label={t('sans.volAria')}
            />
          </label>
        </div>

        <div className="sans-footer">
          <p className="sans-credit">
            {t('sans.credit')}
            <br />
            {t('sans.secret')}
          </p>
          <Link to="/" className="sans-home">
            {t('sans.back')}
          </Link>
        </div>
      </div>
    </div>
  )
}
