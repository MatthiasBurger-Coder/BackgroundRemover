import { usePlaybackState } from '../../context/PlaybackContext'
import { useSourceState } from '../../context/SourceContext'
import { usePreviewVideoController } from '../../hooks/usePreviewVideoController'
import { formatTimecode } from '../../utils/timecode'
import { Panel } from '../layout/Panel'

export function PreviewPlayer() {
  const sourceState = useSourceState()
  const playbackState = usePlaybackState()
  const { adoptCurrentFrame, seekToFrame, stepFrame, togglePlayback, videoRef } =
    usePreviewVideoController()

  const frameCount = sourceState.metadata?.frameCount ?? 0
  const isLoaded = sourceState.sourceUrl !== null

  return (
    <Panel
      title="Preview Player"
      eyebrow="Playback Context"
      actions={
        <div className="chip-row">
          <span className="chip">{playbackState.previewStatus}</span>
          <span className="chip">{playbackState.playbackFrameIndex.toString().padStart(4, '0')}</span>
        </div>
      }
    >
      {isLoaded ? (
        <>
          <div className="viewport viewport--video">
            <video
              ref={videoRef}
              className="viewport__media"
              src={sourceState.sourceUrl ?? undefined}
              preload="metadata"
              playsInline
              muted
              controls={false}
            />
          </div>

          <div className="transport-strip">
            <button className="button" type="button" onClick={() => void togglePlayback()}>
              {playbackState.playbackRunning ? 'Pause' : 'Play'}
            </button>
            <button
              className="button button--ghost"
              type="button"
              onClick={() => stepFrame(-1)}
              disabled={playbackState.playbackRunning || !isLoaded}
            >
              Step -1
            </button>
            <button
              className="button button--ghost"
              type="button"
              onClick={() => stepFrame(1)}
              disabled={playbackState.playbackRunning || !isLoaded}
            >
              Step +1
            </button>
            <button
              className="button button--secondary"
              type="button"
              onClick={() => void adoptCurrentFrame()}
              disabled={!isLoaded}
            >
              Adopt Snapshot
            </button>
          </div>

          <input
            className="timeline"
            type="range"
            min={0}
            max={Math.max(frameCount - 1, 0)}
            value={Math.min(playbackState.playbackFrameIndex, Math.max(frameCount - 1, 0))}
            disabled={playbackState.playbackRunning || frameCount <= 1}
            onChange={(event) => {
              seekToFrame(Number(event.target.value))
            }}
          />

          <dl className="metadata-grid metadata-grid--wide">
            <div>
              <dt>Preview frame</dt>
              <dd>{playbackState.playbackFrameIndex.toString().padStart(4, '0')}</dd>
            </div>
            <div>
              <dt>Timestamp</dt>
              <dd>{formatTimecode(playbackState.playbackTimestampSeconds)}</dd>
            </div>
            <div>
              <dt>Playback FPS</dt>
              <dd>{playbackState.playbackFps.toFixed(2)}</dd>
            </div>
            <div>
              <dt>Rule</dt>
              <dd>Workbench stays fixed while playback runs</dd>
            </div>
          </dl>
        </>
      ) : (
        <div className="viewport viewport--empty">
          <p>Preview playback becomes available after a source asset is registered.</p>
        </div>
      )}
    </Panel>
  )
}
