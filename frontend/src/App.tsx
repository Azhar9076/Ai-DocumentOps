import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Quality } from './pages/Quality'
import { Queue } from './pages/Queue'
import { Upload } from './pages/Upload'
import { Verify } from './pages/Verify'
import { Workflow } from './pages/Workflow'
import { Governance } from './pages/Governance'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="upload" element={<Upload />} />
        <Route path="queue" element={<Queue />} />
        <Route path="documents/:documentId" element={<Verify />} />
        <Route path="workflow" element={<Workflow />} />
        <Route path="quality" element={<Quality />} />
        <Route path="governance" element={<Governance />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
