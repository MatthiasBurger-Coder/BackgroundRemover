import { EditorControls } from '../components/controls/EditorControls'
import { PreviewPlayer } from '../components/preview/PreviewPlayer'
import { SourcePanel } from '../components/source/SourcePanel'
import { WorkbenchPanel } from '../components/workbench/WorkbenchPanel'
import { usePlaybackState } from '../context/PlaybackContext'
import { useSourceState } from '../context/SourceContext'
import { useWorkbenchState } from '../context/WorkbenchContext'
import { formatTimecode } from '../utils/timecode'

export function WorkspacePage() {
  const sourceState = useSourceState()
  const playbackState = usePlaybackState()
  const workbenchState = useWorkbenchState()

  return (
    <main className="workspace-shell">
      <header className="workspace-header">
        <div>
          <p className="workspace-header__eyebrow">Browser Workbench</p>
          <h1>Person Video Extraction Workspace</h1>
          <p className="workspace-header__copy">
            Preview playback remains live. The workbench stays locked to a single adopted frame for
            prompts, overlays, and mask controls.
          </p>
        </div>
        <div className="workspace-header__stats">
          <div>
            <span>Source</span>
            <strong>{sourceState.activeAssetId ? sourceState.videoName : 'Awaiting asset'}</strong>
          </div>
          <div>
            <span>Preview</span>
            <strong>
              {playbackState.playbackFrameIndex.toString().padStart(4, '0')} /{' '}
              {formatTimecode(playbackState.playbackTimestampSeconds)}
            </strong>
          </div>
          <div>
            <span>Workbench</span>
            <strong>
              {workbenchState.workbenchFrameIndex.toString().padStart(4, '0')} /{' '}
              {formatTimecode(workbenchState.workbenchTimestampSeconds)}
            </strong>
          </div>
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="workspace-sidebar">
          <SourcePanel />
          <EditorControls />
        </aside>
        <section className="workspace-main">
          <PreviewPlayer />
          <WorkbenchPanel />
        </section>
      </section>
    </main>
  )
}
