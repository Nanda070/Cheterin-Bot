import { useCallback, useRef } from 'react'

/**
 * Count rapid clicks; fire `onUnlock` when `need` is reached.
 * Gap longer than `gapMs` resets the streak.
 */
export function useSecretClicks(need: number, onUnlock: () => void, gapMs = 1400) {
  const countRef = useRef(0)
  const lastRef = useRef(0)

  return useCallback(() => {
    const now = Date.now()
    if (now - lastRef.current > gapMs) countRef.current = 0
    lastRef.current = now
    countRef.current += 1
    if (countRef.current >= need) {
      countRef.current = 0
      onUnlock()
    }
  }, [need, onUnlock, gapMs])
}
