export function formatTimecode(seconds: number): string {
  const boundedSeconds = Number.isFinite(seconds) ? Math.max(seconds, 0) : 0
  const totalMilliseconds = Math.round(boundedSeconds * 1000)
  const hours = Math.floor(totalMilliseconds / 3_600_000)
  const minutes = Math.floor((totalMilliseconds % 3_600_000) / 60_000)
  const secs = Math.floor((totalMilliseconds % 60_000) / 1000)
  const milliseconds = totalMilliseconds % 1000

  return [
    hours.toString().padStart(2, '0'),
    minutes.toString().padStart(2, '0'),
    secs.toString().padStart(2, '0'),
  ].join(':') + `.${milliseconds.toString().padStart(3, '0')}`
}

export function clampFrameIndex(frameIndex: number, frameCount: number): number {
  if (frameCount <= 0) {
    return 0
  }

  return Math.max(0, Math.min(Math.round(frameIndex), frameCount - 1))
}

export function frameIndexToSeconds(frameIndex: number, fps: number): number {
  if (fps <= 0) {
    return 0
  }

  return clampFrameIndex(frameIndex, Number.MAX_SAFE_INTEGER) / fps
}

export function secondsToFrameIndex(seconds: number, fps: number, frameCount: number): number {
  if (fps <= 0) {
    return 0
  }

  return clampFrameIndex(Math.round(seconds * fps), frameCount)
}
