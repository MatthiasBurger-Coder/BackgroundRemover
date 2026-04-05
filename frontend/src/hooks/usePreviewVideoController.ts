import { useEffect, useEffectEvent, useRef, type MutableRefObject } from 'react'
import { usePlaybackState } from '../context/PlaybackContext'
import { useSourceState } from '../context/SourceContext'
import { useWorkspaceActions } from '../context/WorkspaceActionsContext'
import { clampFrameIndex, secondsToFrameIndex } from '../utils/timecode'

interface PreviewVideoController {
  videoRef: MutableRefObject<HTMLVideoElement | null>
  togglePlayback: () => Promise<void>
  seekToFrame: (frameIndex: number) => void
  stepFrame: (step: number) => void
  adoptCurrentFrame: () => Promise<void>
}

export function usePreviewVideoController(): PreviewVideoController {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const sourceState = useSourceState()
  const playbackState = usePlaybackState()
  const { syncWorkbenchFromPlaybackFrame, updatePlaybackState } = useWorkspaceActions()

  const publishPlaybackTelemetry = useEffectEvent((previewStatus?: 'playing' | 'paused' | 'seeking') => {
    if (sourceState.metadata === null || videoRef.current === null) {
      return
    }

    const frameIndex = secondsToFrameIndex(
      videoRef.current.currentTime,
      sourceState.metadata.fps,
      sourceState.metadata.frameCount,
    )
    updatePlaybackState({
      playbackRunning: !videoRef.current.paused && !videoRef.current.ended,
      playbackFrameIndex: frameIndex,
      playbackTimestampSeconds: videoRef.current.currentTime,
      playbackFps: sourceState.metadata.fps,
      previewStatus: previewStatus ?? (!videoRef.current.paused ? 'playing' : 'paused'),
    })
  })

  const adoptPausedFrame = useEffectEvent(async () => {
    if (sourceState.metadata === null || videoRef.current === null) {
      return
    }

    const frameIndex = secondsToFrameIndex(
      videoRef.current.currentTime,
      sourceState.metadata.fps,
      sourceState.metadata.frameCount,
    )
    await syncWorkbenchFromPlaybackFrame(frameIndex, videoRef.current.currentTime)
  })

  useEffect(() => {
    const videoElement = videoRef.current
    if (videoElement === null) {
      return
    }

    const handlePlay = () => {
      publishPlaybackTelemetry('playing')
    }
    const handlePause = () => {
      publishPlaybackTelemetry('paused')
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
    const handleSeeked = () => {
      publishPlaybackTelemetry(videoElement.paused ? 'paused' : 'playing')
      if (videoElement.paused) {
        void adoptPausedFrame()
      }
    }
    const handleEnded = () => {
      publishPlaybackTelemetry('paused')
      void adoptPausedFrame()
    }

    videoElement.addEventListener('play', handlePlay)
    videoElement.addEventListener('pause', handlePause)
    videoElement.addEventListener('timeupdate', handleTimeUpdate)
    videoElement.addEventListener('seeking', handleSeeking)
    videoElement.addEventListener('seeked', handleSeeked)
    videoElement.addEventListener('ended', handleEnded)

    return () => {
      videoElement.removeEventListener('play', handlePlay)
      videoElement.removeEventListener('pause', handlePause)
      videoElement.removeEventListener('timeupdate', handleTimeUpdate)
      videoElement.removeEventListener('seeking', handleSeeking)
      videoElement.removeEventListener('seeked', handleSeeked)
      videoElement.removeEventListener('ended', handleEnded)
    }
  }, [adoptPausedFrame, publishPlaybackTelemetry, sourceState.activeAssetId])

  useEffect(() => {
    if (videoRef.current === null) {
      return
    }

    videoRef.current.currentTime = 0
    videoRef.current.pause()
  }, [sourceState.sourceUrl])

  const togglePlayback = async () => {
    if (videoRef.current === null || sourceState.metadata === null) {
      return
    }

    if (videoRef.current.paused) {
      await videoRef.current.play()
      return
    }

    videoRef.current.pause()
  }

  const seekToFrame = (frameIndex: number) => {
    if (videoRef.current === null || sourceState.metadata === null || !videoRef.current.paused) {
      return
    }

    const nextFrameIndex = clampFrameIndex(frameIndex, sourceState.metadata.frameCount)
    videoRef.current.currentTime = nextFrameIndex / sourceState.metadata.fps
  }

  const stepFrame = (step: number) => {
    if (sourceState.metadata === null) {
      return
    }

    seekToFrame(playbackState.playbackFrameIndex + step)
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
    togglePlayback,
    seekToFrame,
    stepFrame,
    adoptCurrentFrame,
  }
}
