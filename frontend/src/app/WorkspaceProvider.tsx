import { startTransition, type ReactNode, useState } from 'react'
import { PlaybackContext } from '../context/PlaybackContext'
import { SourceContext } from '../context/SourceContext'
import {
  type WorkspaceActions,
  WorkspaceActionsContext,
} from '../context/WorkspaceActionsContext'
import { WorkbenchContext } from '../context/WorkbenchContext'
import type {
  CreatePromptPayload,
  PreviewStatus,
  UpdateWorkbenchSettingsPayload,
} from '../models/workspace'
import {
  addWorkbenchPrompt,
  clearWorkbenchPrompts,
  deleteAsset,
  refreshWorkbenchPreview,
  registerAsset,
  syncWorkbenchFrame,
  updateWorkbenchSettings as updateWorkbenchSettingsRequest,
} from '../services/api/workspaceApi'
import {
  createEmptyPlaybackState,
  createEmptySourceState,
  createEmptyWorkbenchState,
  mapAssetToSourceState,
  mapPlaybackResponse,
  mapWorkbenchSnapshot,
  mapWorkbenchState,
} from '../services/mapping/workspaceMappers'

function resolveErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.length > 0) {
    return error.message
  }
  return 'Unexpected workspace error'
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [sourceState, setSourceState] = useState(createEmptySourceState)
  const [playbackState, setPlaybackState] = useState(createEmptyPlaybackState)
  const [workbenchState, setWorkbenchState] = useState(createEmptyWorkbenchState)

  const registerSource = async (file: File) => {
    startTransition(() => {
      setSourceState((currentState) => ({
        ...currentState,
        sourceStatus: 'uploading',
        errorMessage: null,
      }))
    })

    try {
      const response = await registerAsset(file)
      const fingerprint = `${file.name}:${file.size}:${file.lastModified}`

      startTransition(() => {
        setSourceState(mapAssetToSourceState(response.asset, fingerprint))
        setPlaybackState(mapPlaybackResponse(response.playback))
        setWorkbenchState(mapWorkbenchSnapshot(response.workbench))
      })
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setSourceState({
          ...createEmptySourceState(),
          sourceStatus: 'error',
          errorMessage: message,
        })
        setPlaybackState(createEmptyPlaybackState())
        setWorkbenchState(createEmptyWorkbenchState())
      })
    }
  }

  const clearSource = async () => {
    const activeAssetId = sourceState.activeAssetId

    try {
      if (activeAssetId !== null) {
        await deleteAsset(activeAssetId)
      }
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setSourceState((currentState) => ({
          ...currentState,
          sourceStatus: 'error',
          errorMessage: message,
        }))
      })
      return
    }

    startTransition(() => {
      setSourceState(createEmptySourceState())
      setPlaybackState(createEmptyPlaybackState())
      setWorkbenchState(createEmptyWorkbenchState())
    })
  }

  const updatePlaybackState = (nextState: {
    playbackRunning?: boolean
    playbackFrameIndex?: number
    playbackTimestampSeconds?: number
    playbackFps?: number
    previewStatus?: PreviewStatus
  }) => {
    startTransition(() => {
      setPlaybackState((currentState) => ({
        playbackRunning: nextState.playbackRunning ?? currentState.playbackRunning,
        playbackFrameIndex: nextState.playbackFrameIndex ?? currentState.playbackFrameIndex,
        playbackTimestampSeconds:
          nextState.playbackTimestampSeconds ?? currentState.playbackTimestampSeconds,
        playbackFps: nextState.playbackFps ?? currentState.playbackFps,
        previewStatus: nextState.previewStatus ?? currentState.previewStatus,
      }))
    })
  }

  const syncWorkbenchFromPlaybackFrame = async (
    frameIndex: number,
    timestampSeconds: number,
  ) => {
    if (sourceState.activeAssetId === null) {
      return
    }

    const requestKey = `${sourceState.activeAssetId}:${frameIndex}`
    if (
      workbenchState.workbenchFrameRequestKey === requestKey &&
      workbenchState.workbenchFrameData !== null
    ) {
      startTransition(() => {
        setWorkbenchState((currentState) => ({
          ...currentState,
          workbenchFrameIndex: frameIndex,
          workbenchTimestampSeconds: timestampSeconds,
          workbenchStatus: 'ready',
          errorMessage: null,
        }))
      })
      return
    }

    startTransition(() => {
      setWorkbenchState((currentState) => ({
        ...currentState,
        workbenchStatus: 'loading',
        errorMessage: null,
      }))
    })

    try {
      const snapshot = await syncWorkbenchFrame(sourceState.activeAssetId, frameIndex)
      startTransition(() => {
        setWorkbenchState(mapWorkbenchSnapshot(snapshot))
      })
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setWorkbenchState((currentState) => ({
          ...currentState,
          workbenchStatus: 'error',
          errorMessage: message,
        }))
      })
    }
  }

  const addPrompt = async (payload: CreatePromptPayload) => {
    if (sourceState.activeAssetId === null) {
      return
    }

    try {
      const state = await addWorkbenchPrompt(sourceState.activeAssetId, payload)
      startTransition(() => {
        setWorkbenchState((currentState) => mapWorkbenchState(state, currentState.workbenchFrameData))
      })
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setWorkbenchState((currentState) => ({
          ...currentState,
          workbenchStatus: 'error',
          errorMessage: message,
        }))
      })
    }
  }

  const clearPrompts = async () => {
    if (sourceState.activeAssetId === null) {
      return
    }

    try {
      const state = await clearWorkbenchPrompts(sourceState.activeAssetId)
      startTransition(() => {
        setWorkbenchState((currentState) => mapWorkbenchState(state, currentState.workbenchFrameData))
      })
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setWorkbenchState((currentState) => ({
          ...currentState,
          workbenchStatus: 'error',
          errorMessage: message,
        }))
      })
    }
  }

  const updateWorkbenchSettings = async (payload: UpdateWorkbenchSettingsPayload) => {
    if (sourceState.activeAssetId === null) {
      return
    }

    try {
      const state = await updateWorkbenchSettingsRequest(sourceState.activeAssetId, payload)
      startTransition(() => {
        setWorkbenchState((currentState) => mapWorkbenchState(state, currentState.workbenchFrameData))
      })
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setWorkbenchState((currentState) => ({
          ...currentState,
          workbenchStatus: 'error',
          errorMessage: message,
        }))
      })
    }
  }

  const refreshPreview = async () => {
    if (sourceState.activeAssetId === null) {
      return
    }

    try {
      const state = await refreshWorkbenchPreview(sourceState.activeAssetId)
      startTransition(() => {
        setWorkbenchState((currentState) => mapWorkbenchState(state, currentState.workbenchFrameData))
      })
    } catch (error) {
      const message = resolveErrorMessage(error)
      startTransition(() => {
        setWorkbenchState((currentState) => ({
          ...currentState,
          workbenchStatus: 'error',
          errorMessage: message,
        }))
      })
    }
  }

  const actions: WorkspaceActions = {
    registerSource,
    clearSource,
    updatePlaybackState,
    syncWorkbenchFromPlaybackFrame,
    addPrompt,
    clearPrompts,
    updateWorkbenchSettings,
    refreshPreview,
  }

  return (
    <SourceContext value={sourceState}>
      <PlaybackContext value={playbackState}>
        <WorkbenchContext value={workbenchState}>
          <WorkspaceActionsContext value={actions}>{children}</WorkspaceActionsContext>
        </WorkbenchContext>
      </PlaybackContext>
    </SourceContext>
  )
}
