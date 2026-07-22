import { Navigate } from 'react-router-dom'

/** Legacy route — welcome settings live on Server Entry. */
export function WelcomePage() {
  return <Navigate to="/server-entry" replace />
}
