import { useState } from 'react'
import { useSourceState } from '../../context/SourceContext'
import { useWorkbenchState } from '../../context/WorkbenchContext'
import { useWorkspaceActions } from '../../context/WorkspaceActionsContext'
import type { MaskSettings, PromptMode } from '../../models/workspace'
import { formatTimecode } from '../../utils/timecode'
import { Panel } from '../layout/Panel'

interface MaskSettingsFormProps {
  disabled: boolean
  initialMaskSettings: MaskSettings
  initialShowDebugOverlay: boolean
  onSubmit: (payload: {
    threshold: number
    feather: number
    invert: boolean
    showDebugOverlay: boolean
  }) => Promise<void>
}

function MaskSettingsForm({
  disabled,
  initialMaskSettings,
  initialShowDebugOverlay,
  onSubmit,
}: MaskSettingsFormProps) {
  const [threshold, setThreshold] = useState(initialMaskSettings.threshold)
  const [feather, setFeather] = useState(initialMaskSettings.feather)
  const [invert, setInvert] = useState(initialMaskSettings.invert)
  const [showDebugOverlay, setShowDebugOverlay] = useState(initialShowDebugOverlay)

  return (
    <form
      className="control-group"
      onSubmit={(event) => {
        event.preventDefault()
        void onSubmit({
          threshold,
          feather,
          invert,
          showDebugOverlay,
        })
      }}
    >
      <p className="label">Mask settings</p>
      <label>
        <span>Threshold</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={threshold}
          onChange={(event) => setThreshold(Number(event.target.value))}
        />
      </label>
      <label>
        <span>Feather</span>
        <input
          type="range"
          min={0}
          max={32}
          step={1}
          value={feather}
          onChange={(event) => setFeather(Number(event.target.value))}
        />
      </label>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={invert}
          onChange={(event) => setInvert(event.target.checked)}
        />
        <span>Invert mask</span>
      </label>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={showDebugOverlay}
          onChange={(event) => setShowDebugOverlay(event.target.checked)}
        />
        <span>Debug overlay</span>
      </label>
      <button className="button" type="submit" disabled={disabled}>
        Apply Settings
      </button>
    </form>
  )
}

export function EditorControls() {
  const sourceState = useSourceState()
  const workbenchState = useWorkbenchState()
  const { addPrompt, clearPrompts, refreshPreview, updateWorkbenchSettings } = useWorkspaceActions()

  const [promptMode, setPromptMode] = useState<PromptMode>('foreground')
  const [promptX, setPromptX] = useState(320)
  const [promptY, setPromptY] = useState(180)
  const settingsDraftKey = [
    sourceState.activeAssetId ?? 'none',
    workbenchState.selectedMaskSettings.threshold.toFixed(2),
    workbenchState.selectedMaskSettings.feather,
    workbenchState.selectedMaskSettings.invert ? 'invert' : 'normal',
    workbenchState.overlayState.showDebugOverlay ? 'overlay-on' : 'overlay-off',
  ].join(':')

  return (
    <Panel title="Editor Controls" eyebrow="Workbench Context">
      <div className="control-group">
        <p className="label">Workbench target</p>
        <div className="workbench-target">
          <strong>{workbenchState.workbenchFrameIndex.toString().padStart(4, '0')}</strong>
          <span>{formatTimecode(workbenchState.workbenchTimestampSeconds)}</span>
        </div>
      </div>

      <form
        className="control-group"
        onSubmit={(event) => {
          event.preventDefault()
          void addPrompt({
            mode: promptMode,
            x: promptX,
            y: promptY,
          })
        }}
      >
        <p className="label">Prompt mode</p>
        <div className="segmented-control">
          {(['foreground', 'background'] as const).map((mode) => (
            <button
              key={mode}
              className={`segmented-control__item${
                promptMode === mode ? ' segmented-control__item--active' : ''
              }`}
              type="button"
              onClick={() => setPromptMode(mode)}
            >
              {mode}
            </button>
          ))}
        </div>

        <div className="field-row">
          <label>
            <span>X</span>
            <input
              type="number"
              min={0}
              max={sourceState.metadata?.width ?? 4096}
              value={promptX}
              onChange={(event) => setPromptX(Number(event.target.value))}
            />
          </label>
          <label>
            <span>Y</span>
            <input
              type="number"
              min={0}
              max={sourceState.metadata?.height ?? 4096}
              value={promptY}
              onChange={(event) => setPromptY(Number(event.target.value))}
            />
          </label>
        </div>

        <button className="button" type="submit" disabled={sourceState.activeAssetId === null}>
          Add Prompt
        </button>
      </form>

      <MaskSettingsForm
        key={settingsDraftKey}
        disabled={sourceState.activeAssetId === null}
        initialMaskSettings={workbenchState.selectedMaskSettings}
        initialShowDebugOverlay={workbenchState.overlayState.showDebugOverlay}
        onSubmit={updateWorkbenchSettings}
      />

      <div className="control-actions">
        <button
          className="button button--secondary"
          type="button"
          onClick={() => void refreshPreview()}
          disabled={sourceState.activeAssetId === null}
        >
          Generate Mask Preview
        </button>
        <button
          className="button button--ghost"
          type="button"
          onClick={() => void clearPrompts()}
          disabled={sourceState.activeAssetId === null || workbenchState.promptEntries.length === 0}
        >
          Clear Prompts
        </button>
      </div>

      <div className="prompt-log">
        <p className="label">Prompt log</p>
        {workbenchState.promptEntries.length > 0 ? (
          <ul>
            {workbenchState.promptEntries.map((prompt) => (
              <li key={prompt.identifier}>
                {prompt.mode} frame {prompt.frameIndex.toString().padStart(4, '0')} @ {prompt.x},{' '}
                {prompt.y}
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-copy">Prompt entries stay bound to the fixed workbench frame.</p>
        )}
      </div>
    </Panel>
  )
}
