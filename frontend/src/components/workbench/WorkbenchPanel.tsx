import { useSourceState } from '../../context/SourceContext'
import { useWorkbenchState } from '../../context/WorkbenchContext'
import { formatTimecode } from '../../utils/timecode'
import { Panel } from '../layout/Panel'

export function WorkbenchPanel() {
  const sourceState = useSourceState()
  const workbenchState = useWorkbenchState()

  return (
    <Panel
      title="Workbench"
      eyebrow="Fixed Snapshot"
      actions={
        <div className="chip-row">
          <span className="chip">{workbenchState.workbenchStatus}</span>
          <span className="chip">{workbenchState.promptEntries.length} prompts</span>
        </div>
      }
    >
      {workbenchState.workbenchFrameData ? (
        <>
          <div className="viewport viewport--image">
            <img
              className="viewport__media"
              src={workbenchState.workbenchFrameData.imageDataUrl}
              alt={`Workbench frame ${workbenchState.workbenchFrameIndex}`}
            />
            <div
              className={`overlay-layer${
                workbenchState.overlayState.showDebugOverlay ? ' overlay-layer--debug' : ''
              }`}
            >
              {workbenchState.promptEntries.map((prompt) => {
                const width = workbenchState.workbenchFrameData?.width ?? 1
                const height = workbenchState.workbenchFrameData?.height ?? 1
                const left = (prompt.x / width) * 100
                const top = (prompt.y / height) * 100
                return (
                  <span
                    key={prompt.identifier}
                    className={`prompt-marker prompt-marker--${prompt.mode}`}
                    style={{ left: `${left}%`, top: `${top}%` }}
                    title={`${prompt.mode} @ ${prompt.x}, ${prompt.y}`}
                  />
                )
              })}
            </div>
          </div>

          <dl className="metadata-grid metadata-grid--wide">
            <div>
              <dt>Workbench frame</dt>
              <dd>{workbenchState.workbenchFrameIndex.toString().padStart(4, '0')}</dd>
            </div>
            <div>
              <dt>Timecode</dt>
              <dd>{formatTimecode(workbenchState.workbenchTimestampSeconds)}</dd>
            </div>
            <div>
              <dt>Request key</dt>
              <dd>{workbenchState.workbenchFrameRequestKey ?? 'n/a'}</dd>
            </div>
            <div>
              <dt>Source</dt>
              <dd>{sourceState.videoName}</dd>
            </div>
          </dl>
        </>
      ) : (
        <div className="viewport viewport--empty">
          <p>The workbench remains empty until a paused or selected preview frame is adopted.</p>
        </div>
      )}

      {workbenchState.errorMessage ? <p className="error-copy">{workbenchState.errorMessage}</p> : null}
    </Panel>
  )
}
