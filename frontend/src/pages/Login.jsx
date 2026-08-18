import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Login.css'

export default function Login() {
  const { user, signInWithUsername, signUp } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('signin')

  const [signinUsername, setSigninUsername] = useState('')
  const [signinPassword, setSigninPassword] = useState('')
  const [signinError, setSigninError] = useState('')
  const [signinBusy, setSigninBusy] = useState(false)

  const [newUsername, setNewUsername] = useState('')
  const [newName, setNewName] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [signupError, setSignupError] = useState('')
  const [signupBusy, setSignupBusy] = useState(false)

  if (user) return <Navigate to="/home" replace />

  async function handleSignIn(e) {
    e.preventDefault()
    setSigninError('')
    setSigninBusy(true)
    try {
      await signInWithUsername(signinUsername, signinPassword)
      navigate('/home')
    } catch (err) {
      setSigninError(err.message || 'Invalid username or password.')
    } finally {
      setSigninBusy(false)
    }
  }

  async function handleSignUp(e) {
    e.preventDefault()
    setSignupError('')

    if (!newUsername.trim()) return setSignupError('Username is required.')
    if (!newEmail.trim()) return setSignupError('Email is required.')
    if (!newPassword) return setSignupError('Password is required.')
    if (newPassword !== newPasswordConfirm) return setSignupError("Passwords don't match.")

    setSignupBusy(true)
    try {
      await signUp({ username: newUsername, displayName: newName, email: newEmail, password: newPassword })
      navigate('/home')
    } catch (err) {
      setSignupError(`Could not create account: ${err.message || err}`)
    } finally {
      setSignupBusy(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>The Field 🏈</h1>
        <hr />

        <div className="tabs">
          <button className={tab === 'signin' ? 'tab active' : 'tab'} onClick={() => setTab('signin')}>
            Sign in
          </button>
          <button className={tab === 'signup' ? 'tab active' : 'tab'} onClick={() => setTab('signup')}>
            Create account
          </button>
        </div>

        {tab === 'signin' && (
          <form onSubmit={handleSignIn}>
            <label>
              Username <span className="required">*</span>
              <input value={signinUsername} onChange={(e) => setSigninUsername(e.target.value)} autoFocus />
            </label>
            <label>
              Password <span className="required">*</span>
              <input type="password" value={signinPassword} onChange={(e) => setSigninPassword(e.target.value)} />
            </label>
            {signinError && <p className="error">{signinError}</p>}
            <button type="submit" className="primary" disabled={signinBusy}>
              {signinBusy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        )}

        {tab === 'signup' && (
          <form onSubmit={handleSignUp}>
            <label>
              Username <span className="required">*</span>
              <input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} />
            </label>
            <label>
              Name
              <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="What should we call you?" />
            </label>
            <label>
              Email <span className="required">*</span>
              <input value={newEmail} onChange={(e) => setNewEmail(e.target.value)} />
            </label>
            <label>
              Password <span className="required">*</span>
              <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
            </label>
            <label>
              Confirm password <span className="required">*</span>
              <input type="password" value={newPasswordConfirm} onChange={(e) => setNewPasswordConfirm(e.target.value)} />
            </label>
            {signupError && <p className="error">{signupError}</p>}
            <button type="submit" className="primary" disabled={signupBusy}>
              {signupBusy ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
