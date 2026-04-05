import { WorkspaceProvider } from './app/WorkspaceProvider'
import { WorkspacePage } from './pages/WorkspacePage'

function App() {
  return (
    <WorkspaceProvider>
      <WorkspacePage />
    </WorkspaceProvider>
  )
}

export default App
