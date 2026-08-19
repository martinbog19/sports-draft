import { useState } from 'react'
import { Modal } from './Modal'
import { deleteRoom } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function DeleteRoomModal({ room, onClose, onDeleted }) {
  const { user } = useAuth()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const name = room.draft_name || room.code

  async function handleDelete() {
    setBusy(true)
    setError('')
    try {
      await deleteRoom(room.code, user.id)
      onDeleted()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Delete draft" onClose={onClose}>
      <p className="warning">
        Delete <strong>{name}</strong>? This cannot be undone.
      </p>
      {error && <p className="error">{error}</p>}
      <div className="modal-actions">
        <button className="secondary" onClick={onClose}>
          Cancel
        </button>
        <button className="primary" disabled={busy} onClick={handleDelete}>
          {busy ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </Modal>
  )
}
