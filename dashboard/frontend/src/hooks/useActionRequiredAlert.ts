import { useEffect, useRef, useState } from 'react'

const MUTE_KEY = 'gameActionAlertMuted'

function readMuted(): boolean {
  try {
    return window.localStorage.getItem(MUTE_KEY) === '1'
  } catch {
    return false
  }
}

function writeMuted(value: boolean) {
  try {
    window.localStorage.setItem(MUTE_KEY, value ? '1' : '0')
  } catch {
    // localStorage unavailable (private mode, test env) — mute just won't persist across reloads.
  }
}

function beep() {
  try {
    const AudioContextClass = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AudioContextClass) return
    const ctx = new AudioContextClass()
    const oscillator = ctx.createOscillator()
    const gain = ctx.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.value = 880
    gain.gain.value = 0.15
    oscillator.connect(gain)
    gain.connect(ctx.destination)
    oscillator.start()
    oscillator.stop(ctx.currentTime + 0.25)
    oscillator.onended = () => ctx.close()
  } catch {
    // Web Audio unsupported or blocked by autoplay policy — skip the beep silently.
  }
}

/**
 * Plays a short beep and, while the tab is hidden, flashes `document.title` whenever
 * `actionRequired` flips from false to true — so a player waiting on their turn (mafia
 * night action, bunker vote, etc.) notices without staring at the tab. Mute preference
 * is persisted in localStorage and shared across all game pages.
 */
export function useActionRequiredAlert(actionRequired: boolean, alertTitle: string) {
  const [muted, setMuted] = useState(readMuted)
  const wasRequiredRef = useRef(actionRequired)
  const originalTitleRef = useRef<string | null>(null)
  const flashTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopFlash = () => {
    if (flashTimerRef.current) {
      clearInterval(flashTimerRef.current)
      flashTimerRef.current = null
    }
    if (originalTitleRef.current !== null) {
      document.title = originalTitleRef.current
      originalTitleRef.current = null
    }
  }

  const toggleMuted = () => {
    setMuted((prev) => {
      const next = !prev
      writeMuted(next)
      return next
    })
  }

  useEffect(() => {
    const becameRequired = actionRequired && !wasRequiredRef.current
    wasRequiredRef.current = actionRequired

    if (!actionRequired) {
      stopFlash()
      return
    }

    if (becameRequired && !muted) {
      beep()
      if (document.hidden) {
        originalTitleRef.current = document.title
        let flashOn = false
        flashTimerRef.current = setInterval(() => {
          flashOn = !flashOn
          document.title = flashOn ? alertTitle : (originalTitleRef.current as string)
        }, 1000)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally only re-runs on the false→true edge
  }, [actionRequired, muted, alertTitle])

  useEffect(() => {
    function onVisibilityChange() {
      if (!document.hidden) stopFlash()
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => document.removeEventListener('visibilitychange', onVisibilityChange)
  }, [])

  useEffect(() => stopFlash, [])

  return { muted, toggleMuted }
}
