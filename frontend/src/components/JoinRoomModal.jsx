import { useState } from 'react'
import { Modal } from './Modal'
import { joinRoom } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function JoinRoomModal({ onClose, onJoined }) {
  const { user } = useAuth()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleJoin() {
    if (!code.trim()) {
      setError('Enter a room code.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const displayName = user.display_name || user.email.split('@')[0]
      await joinRoom(user.id, code.trim().toUpperCase(), displayName)
      onJoined()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Join a draft" onClose={onClose}>
      <input
        placeholder="e.g. ABCDEF"
        maxLength={6}
        value={code}
        onChange={(e) => setCode(e.target.value)}
        autoFocus
      />
      {error && <p className="error">{error}</p>}
      <button className="primary" disabled={busy} onClick={handleJoin}>
        {busy ? 'Joining…' : 'Join'}
      </button>
    </Modal>
  )
}
