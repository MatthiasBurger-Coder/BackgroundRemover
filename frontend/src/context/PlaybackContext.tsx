import { createContext, useContext } from 'react'
import type { PlaybackState } from '../models/workspace'

export const PlaybackContext = createContext<PlaybackState | null>(null)

export function usePlaybackState(): PlaybackState {
  const context = useContext(PlaybackContext)
  if (context === null) {
    throw new Error('usePlaybackState must be used within WorkspaceProvider')
  }
  return context
}
