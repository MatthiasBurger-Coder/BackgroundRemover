import { createContext, useContext } from 'react'
import type {
  CreatePromptPayload,
  PreviewStatus,
  UpdateWorkbenchSettingsPayload,
} from '../models/workspace'

export interface WorkspaceActions {
  registerSource: (file: File) => Promise<void>
  clearSource: () => Promise<void>
  updatePlaybackState: (nextState: {
    playbackRunning?: boolean
    playbackFrameIndex?: number
    playbackTimestampSeconds?: number
    playbackFps?: number
    previewStatus?: PreviewStatus
  }) => void
  syncWorkbenchFromPlaybackFrame: (frameIndex: number, timestampSeconds: number) => Promise<void>
  addPrompt: (payload: CreatePromptPayload) => Promise<void>
  clearPrompts: () => Promise<void>
  updateWorkbenchSettings: (payload: UpdateWorkbenchSettingsPayload) => Promise<void>
  refreshPreview: () => Promise<void>
}

export const WorkspaceActionsContext = createContext<WorkspaceActions | null>(null)

export function useWorkspaceActions(): WorkspaceActions {
  const context = useContext(WorkspaceActionsContext)
  if (context === null) {
    throw new Error('useWorkspaceActions must be used within WorkspaceProvider')
  }
  return context
}
