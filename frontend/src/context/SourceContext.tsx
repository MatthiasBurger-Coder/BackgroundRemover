import { createContext, useContext } from 'react'
import type { SourceState } from '../models/workspace'

export const SourceContext = createContext<SourceState | null>(null)

export function useSourceState(): SourceState {
  const context = useContext(SourceContext)
  if (context === null) {
    throw new Error('useSourceState must be used within WorkspaceProvider')
  }
  return context
}
