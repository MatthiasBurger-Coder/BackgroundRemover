import { useCallback, useEffect, useEffectEvent, useRef, useState, type MutableRefObject } from 'react'
import { usePlaybackState } from '../context/PlaybackContext'
import { useSourceState } from '../context/SourceContext'
import { useWorkspaceActions } from '../context/WorkspaceActionsContext'
import type { VideoFrameData } from '../models/workspace'
import { getFrame } from '../services/api/workspaceApi'
import { clampFrameIndex, frameIndexToSeconds, secondsToFrameIndex } from '../utils/timecode'

interface PreviewVideoController {
  videoRef: MutableRefObject<HTMLVideoElement | null>
  exactPreviewFrame: VideoFrameData | null
  togglePlayback: () => Promise<void>
  seekToFrame: (frameIndex: number) => Promise<void>
  stepFrame: (step: number) => Promise<void>
  adoptCurrentFrame: () => Promise<void>
}

export function usePreviewVideoController(): PreviewVideoController {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const exactPreviewRequestIdRef = useRef(0)
  const exactPreviewPositionRef = useRef<{ frameIndex: number; timestampSeconds: number } | null>(null)
  const sourceState = useSourceState()
  const playbackState = usePlaybackState()
  const { syncWorkbenchFromPlaybackFrame, updatePlaybackState } = useWorkspaceActions()
  const [exactPreviewFrame, setExactPreviewFrame] = useState<VideoFrameData | null>(null)

  const publishPlaybackTelemetry = useEffectEvent((previewStatus?: 'playing' | 'paused' | 'seeking') => {
    if (sourceState.metadata === null || videoRef.current === null) {
      return
    }

    const exactPreviewPosition =
      videoRef.current.paused || previewStatus === 'seeking' ? exactPreviewPositionRef.current : null
    const frameIndex =
      exactPreviewPosition?.frameIndex ??
      secondsToFrameIndex(
        videoRef.current.currentTime,
        sourceState.metadata.fps,
        sourceState.metadata.frameCount,
      )
    const timestampSeconds = exactPreviewPosition?.timestampSeconds ?? videoRef.current.currentTime
    updatePlaybackState({
      playbackRunning: !videoRef.current.paused && !videoRef.current.ended,
      playbackFrameIndex: frameIndex,
      playbackTimestampSeconds: timestampSeconds,
      playbackFps: sourceState.metadata.fps,
      previewStatus: previewStatus ?? (!videoRef.current.paused ? 'playing' : 'paused'),
    })
  })

  const resolveCurrentFrameIndex = useEffectEvent((): number | null => {
    if (sourceState.metadata === null || videoRef.current === null) {
      return null
    }

    return secondsToFrameIndex(
      videoRef.current.currentTime,
      sourceState.metadata.fps,
      sourceState.metadata.frameCount,
    )
  })

  const clearExactPreviewFrame = useCallback(() => {
    exactPreviewRequestIdRef.current += 1
    exactPreviewPositionRef.current = null
    setExactPreviewFrame(null)
  }, [])

  const loadExactPreviewFrame = useCallback(async (frameIndex: number) => {
    if (sourceState.activeAssetId === null) {
      return
    }

    const requestId = exactPreviewRequestIdRef.current + 1
    exactPreviewRequestIdRef.current = requestId
    try {
      const frame = await getFrame(sourceState.activeAssetId, frameIndex)
      if (exactPreviewRequestIdRef.current !== requestId) {
        return
      }
      exactPreviewPositionRef.current = {
        frameIndex: frame.frameIndex,
        timestampSeconds: frame.timestampSeconds,
      }
      setExactPreviewFrame(frame)
    } catch {
      if (exactPreviewRequestIdRef.current !== requestId) {
        return
      }
      exactPreviewPositionRef.current = null
      setExactPreviewFrame(null)
    }
  }, [sourceState.activeAssetId])

  const adoptPausedFrame = useEffectEvent(async () => {
    const frameIndex = resolveCurrentFrameIndex()
    if (frameIndex === null || videoRef.current === null) {
      return
    }

    await syncWorkbenchFromPlaybackFrame(frameIndex, videoRef.current.currentTime)
  })

  useEffect(() => {
    const videoElement = videoRef.current
    if (videoElement === null) {
      return
    }

    const handlePlay = () => {
      clearExactPreviewFrame()
      publishPlaybackTelemetry('playing')
    }
    const handlePause = () => {
      publishPlaybackTelemetry('paused')
      const frameIndex = resolveCurrentFrameIndex()
      if (frameIndex !== null) {
        void loadExactPreviewFrame(frameIndex)
      }
      void adoptPausedFrame()
    }
    const handleTimeUpdate = () => {
      if (!videoElement.paused) {
        publishPlaybackTelemetry('playing')
      }
    }
    const handleSeeking = () => {
      publishPlaybackTelemetry('seeking')
    }
    const handleLoadedMetadata = () => {
      publishPlaybackTelemetry('paused')
      const frameIndex = resolveCurrentFrameIndex()
      if (frameIndex !== null) {
        void loadExactPreviewFrame(frameIndex)
      }
    }
    const handleSeeked = () => {
      publishPlaybackTelemetry(videoElement.paused ? 'paused' : 'playing')
      if (videoElement.paused) {
        const frameIndex = resolveCurrentFrameIndex()
        if (frameIndex !== null) {
          void loadExactPreviewFrame(frameIndex)
        }
        void adoptPausedFrame()
      }
    }
    const handleEnded = () => {
      publishPlaybackTelemetry('paused')
      const frameIndex = resolveCurrentFrameIndex()
      if (frameIndex !== null) {
        void loadExactPreviewFrame(frameIndex)
      }
      void adoptPausedFrame()
    }

    videoElement.addEventListener('play', handlePlay)
    videoElement.addEventListener('pause', handlePause)
    videoElement.addEventListener('timeupdate', handleTimeUpdate)
    videoElement.addEventListener('seeking', handleSeeking)
    videoElement.addEventListener('loadedmetadata', handleLoadedMetadata)
    videoElement.addEventListener('seeked', handleSeeked)
    videoElement.addEventListener('ended', handleEnded)

    return () => {
      videoElement.removeEventListener('play', handlePlay)
      videoElement.removeEventListener('pause', handlePause)
      videoElement.removeEventListener('timeupdate', handleTimeUpdate)
      videoElement.removeEventListener('seeking', handleSeeking)
      videoElement.removeEventListener('loadedmetadata', handleLoadedMetadata)
      videoElement.removeEventListener('seeked', handleSeeked)
      videoElement.removeEventListener('ended', handleEnded)
    }
  }, [clearExactPreviewFrame, loadExactPreviewFrame, sourceState.activeAssetId])

  useEffect(() => {
    if (videoRef.current === null) {
      return
    }

    exactPreviewRequestIdRef.current += 1
    exactPreviewPositionRef.current = null
    videoRef.current.currentTime = 0
    videoRef.current.pause()
  }, [sourceState.sourceUrl])

  const togglePlayback = async () => {
    if (videoRef.current === null || sourceState.metadata === null) {
      return
    }

    if (videoRef.current.paused) {
      clearExactPreviewFrame()
      await videoRef.current.play()
      return
    }

    videoRef.current.pause()
  }

  const seekToFrame = async (frameIndex: number) => {
    if (videoRef.current === null || sourceState.metadata === null || !videoRef.current.paused) {
      return
    }

    const nextFrameIndex = clampFrameIndex(frameIndex, sourceState.metadata.frameCount)
    const targetSeconds =
      frameIndexToSeconds(nextFrameIndex, sourceState.metadata.fps) + (0.5 / sourceState.metadata.fps)
    exactPreviewPositionRef.current = {
      frameIndex: nextFrameIndex,
      timestampSeconds: targetSeconds,
    }
    updatePlaybackState({
      playbackRunning: false,
      playbackFrameIndex: nextFrameIndex,
      playbackTimestampSeconds: targetSeconds,
      playbackFps: sourceState.metadata.fps,
      previewStatus: 'seeking',
    })
    videoRef.current.currentTime = targetSeconds
    await loadExactPreviewFrame(nextFrameIndex)
  }

  const stepFrame = async (step: number) => {
    if (sourceState.metadata === null) {
      return
    }

    const currentFrameIndex =
      exactPreviewPositionRef.current?.frameIndex ??
      exactPreviewFrame?.frameIndex ??
      playbackState.playbackFrameIndex
    await seekToFrame(currentFrameIndex + step)
  }

  const adoptCurrentFrame = async () => {
    if (videoRef.current === null || sourceState.metadata === null) {
      return
    }

    const frameIndex = secondsToFrameIndex(
      videoRef.current.currentTime,
      sourceState.metadata.fps,
      sourceState.metadata.frameCount,
    )
    await syncWorkbenchFromPlaybackFrame(frameIndex, videoRef.current.currentTime)
  }

  return {
    videoRef,
    exactPreviewFrame,
    togglePlayback,
    seekToFrame,
    stepFrame,
    adoptCurrentFrame,
  }
}
