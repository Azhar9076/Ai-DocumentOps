import React, { createContext, useContext, useEffect, useState } from 'react'

export type UserRole = 'admin' | 'reviewer'

interface AuthContextType {
  role: UserRole
  setRole: (role: UserRole) => void
  userEmail: string
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType>({
  role: 'admin',
  setRole: () => {},
  userEmail: 'admin@documentops.ai',
  isAdmin: true,
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<UserRole>(() => {
    return (localStorage.getItem('docops_role') as UserRole) || 'admin'
  })

  useEffect(() => {
    localStorage.setItem('docops_role', role)
  }, [role])

  const userEmail = role === 'admin' ? 'admin@documentops.ai' : 'reviewer@documentops.ai'

  return (
    <AuthContext.Provider
      value={{
        role,
        setRole: setRoleState,
        userEmail,
        isAdmin: role === 'admin',
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
