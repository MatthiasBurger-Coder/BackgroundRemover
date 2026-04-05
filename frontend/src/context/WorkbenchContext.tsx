import { createContext, useContext } from 'react'
import type { WorkbenchState } from '../models/workspace'

export const WorkbenchContext = createContext<WorkbenchState | null>(null)

export function useWorkbenchState(): WorkbenchState {
  const context = useContext(WorkbenchContext)
  if (context === null) {
    throw new Error('useWorkbenchState must be used within WorkspaceProvider')
  }
  return context
}
