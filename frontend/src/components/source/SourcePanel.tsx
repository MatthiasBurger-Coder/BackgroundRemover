import { type ChangeEvent, useRef } from 'react'
import { usePlaybackState } from '../../context/PlaybackContext'
import { useSourceState } from '../../context/SourceContext'
import { useWorkspaceActions } from '../../context/WorkspaceActionsContext'
import { Panel } from '../layout/Panel'

export function SourcePanel() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const sourceState = useSourceState()
  const playbackState = usePlaybackState()
  const { clearSource, registerSource } = useWorkspaceActions()

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file === undefined) {
      return
    }

    await registerSource(file)
    event.target.value = ''
  }

  return (
    <Panel
      title="Source Panel"
      eyebrow="Asset"
      actions={
        <button
          className="button button--ghost"
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={sourceState.sourceStatus === 'uploading'}
        >
          {sourceState.sourceStatus === 'uploading' ? 'Uploading' : 'Select Video'}
        </button>
      }
    >
      <input
        ref={fileInputRef}
        className="sr-only"
        type="file"
        accept="video/mp4,video/quicktime,video/x-matroska,video/x-msvideo"
        onChange={(event) => {
          void handleFileChange(event)
        }}
      />

      <div className="source-summary">
        <div>
          <span className="label">Active asset</span>
          <strong>{sourceState.videoName}</strong>
        </div>
        <div>
          <span className="label">Status</span>
          <strong>{sourceState.sourceStatus}</strong>
        </div>
        <div>
          <span className="label">Playback</span>
          <strong>{playbackState.previewStatus}</strong>
        </div>
      </div>

      {sourceState.metadata ? (
        <dl className="metadata-grid">
          <div>
            <dt>Asset ID</dt>
            <dd>{sourceState.metadata.assetId.slice(0, 8)}</dd>
          </div>
          <div>
            <dt>Resolution</dt>
            <dd>
              {sourceState.metadata.width} x {sourceState.metadata.height}
            </dd>
          </div>
          <div>
            <dt>Frames</dt>
            <dd>{sourceState.metadata.frameCount}</dd>
          </div>
          <div>
            <dt>FPS</dt>
            <dd>{sourceState.metadata.fps.toFixed(2)}</dd>
          </div>
        </dl>
      ) : (
        <p className="empty-copy">
          Register a source video to unlock preview playback and a fixed workbench snapshot.
        </p>
      )}

      {sourceState.errorMessage ? <p className="error-copy">{sourceState.errorMessage}</p> : null}

      <button
        className="button button--secondary"
        type="button"
        onClick={() => {
          void clearSource()
        }}
        disabled={sourceState.activeAssetId === null}
      >
        Remove Source
      </button>
    </Panel>
  )
}
