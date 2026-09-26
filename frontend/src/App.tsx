import { Navigate, Route, Routes } from 'react-router-dom'
import { GovernanceTrustTab } from './components/GovernanceTrustTab'
import { Layout } from './components/Layout'
import { AuthProvider } from './lib/authContext'
import { Dashboard } from './pages/Dashboard'
import { Quality } from './pages/Quality'
import { Queue } from './pages/Queue'
import { StressTest } from './pages/StressTest'
import { Upload } from './pages/Upload'
import { Verify } from './pages/Verify'
import { Workflow } from './pages/Workflow'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<Upload />} />
          <Route path="queue" element={<Queue />} />
          <Route path="documents/:documentId" element={<Verify />} />
          <Route path="workflow" element={<Workflow />} />
          <Route path="quality" element={<Quality />} />
          <Route path="stress-test" element={<StressTest />} />
          <Route path="governance" element={<GovernanceTrustTab />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
