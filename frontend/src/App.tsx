import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './App.css'

import { Dashboard } from './components/Dashboard'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <main className="app">
        <header className="app-header">
          <h1>Clinical Trial Tracker</h1>
          <p className="app-tagline">
            Personalized HER2+ breast cancer trial matching with transparent
            eligibility rationale
          </p>
        </header>
        <Dashboard />
      </main>
    </QueryClientProvider>
  )
}

export default App
