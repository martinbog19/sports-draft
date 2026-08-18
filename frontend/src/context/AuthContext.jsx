import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabaseClient'

const AuthContext = createContext(null)

async function loadProfile(userId) {
  const { data, error } = await supabase
    .from('profiles')
    .select('user_id, username, display_name, email')
    .eq('user_id', userId)
    .single()
  if (error) throw error
  return { id: data.user_id, username: data.username, display_name: data.display_name, email: data.email }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function restore() {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.user && !cancelled) {
        try {
          setUser(await loadProfile(session.user.id))
        } catch {
          setUser(null)
        }
      }
      if (!cancelled) setLoading(false)
    }
    restore()

    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session?.user) setUser(null)
    })

    return () => {
      cancelled = true
      listener.subscription.unsubscribe()
    }
  }, [])

  async function signInWithUsername(username, password) {
    const clean = username.trim().toLowerCase()
    const { data: profile, error: lookupError } = await supabase
      .from('profiles')
      .select('email, display_name')
      .eq('username', clean)
      .single()
    if (lookupError || !profile) throw new Error('Username not found.')

    const { data, error } = await supabase.auth.signInWithPassword({
      email: profile.email,
      password,
    })
    if (error) throw new Error('Invalid username or password.')

    const loaded = await loadProfile(data.user.id)
    setUser(loaded)
    return loaded
  }

  async function signUp({ username, displayName, email, password }) {
    const clean = username.trim().toLowerCase()
    const cleanEmail = email.trim().toLowerCase()
    const name = displayName.trim() || clean

    const { data, error } = await supabase.auth.signUp({ email: cleanEmail, password })
    if (error) throw error
    if (!data.user) throw new Error('Check your email to confirm your account, then sign in.')

    const { error: insertError } = await supabase.from('profiles').insert({
      user_id: data.user.id,
      username: clean,
      display_name: name,
      email: cleanEmail,
    })
    if (insertError) throw insertError

    const loaded = { id: data.user.id, username: clean, display_name: name, email: cleanEmail }
    setUser(loaded)
    return loaded
  }

  async function signOut() {
    await supabase.auth.signOut()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, signInWithUsername, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
