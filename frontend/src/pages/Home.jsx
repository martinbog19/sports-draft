import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { listRooms, getRoomPlayers, startDraft } from '../lib/api'
import { RoomCard } from '../components/RoomCard'
import { JoinRoomModal } from '../components/JoinRoomModal'
import { EditRoomModal } from '../components/EditRoomModal'
import { DeleteRoomModal } from '../components/DeleteRoomModal'
import './Home.css'

export default function Home() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const [rooms, setRooms] = useState([])
  const [playerCounts, setPlayerCounts] = useState({})
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)

  const [showJoin, setShowJoin] = useState(false)
  const [editingRoom, setEditingRoom] = useState(null)
  const [deletingRoom, setDeletingRoom] = useState(null)
  const [launchError, setLaunchError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const { rooms: data } = await listRooms(user.id)
      const sorted = [...data].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
      setRooms(sorted)

      const counts = {}
      await Promise.all(
        sorted.map(async (room) => {
          const { players } = await getRoomPlayers(room.code)
          counts[room.code] = players.length
        })
      )
      setPlayerCounts(counts)
      setLoadError('')
    } catch (err) {
      setLoadError(`Could not load drafts — make sure the backend is running. [${err.message}]`)
    } finally {
      setLoading(false)
    }
  }, [user.id])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function handleLaunch(room) {
    setLaunchError('')
    try {
      await startDraft(room.code, user.id)
      navigate('/draft', { state: { room: { ...room, status: 'drafting' } } })
    } catch (err) {
      setLaunchError(err.message)
    }
  }

  const greeting = user.display_name || user.username

  return (
    <div className="home-page">
      <header className="home-header">
        <h2>Welcome to the field, {greeting}!</h2>
        <div className="home-user">
          <span>{user.username || user.email}</span>
          <button className="secondary" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>

      <div className="home-actions">
        <button className="primary" onClick={() => navigate('/start')}>
          ＋ Create new draft
        </button>
        <button className="secondary" onClick={() => setShowJoin(true)}>
          Enter a code
        </button>
      </div>

      {launchError && <p className="error">{launchError}</p>}

      <h3>My drafts</h3>

      {loading && <p className="muted">Loading…</p>}
      {loadError && <p className="warning-text">{loadError}</p>}
      {!loading && !loadError && rooms.length === 0 && (
        <p className="muted">No drafts yet. Create one or join with a code.</p>
      )}

      <div className="room-grid">
        {rooms.map((room) => (
          <RoomCard
            key={room.id}
            room={room}
            playerCount={playerCounts[room.code] ?? 0}
            isHost={room.host_id === user.id}
            onEdit={() => setEditingRoom(room)}
            onDelete={() => setDeletingRoom(room)}
            onLaunch={() => handleLaunch(room)}
            onOpen={() => navigate('/draft', { state: { room } })}
            onResults={() => navigate('/results', { state: { roomId: room.id } })}
          />
        ))}
      </div>

      {showJoin && (
        <JoinRoomModal
          onClose={() => setShowJoin(false)}
          onJoined={() => {
            setShowJoin(false)
            refresh()
          }}
        />
      )}

      {editingRoom && (
        <EditRoomModal
          room={editingRoom}
          onClose={() => setEditingRoom(null)}
          onSaved={() => {
            setEditingRoom(null)
            refresh()
          }}
        />
      )}

      {deletingRoom && (
        <DeleteRoomModal
          room={deletingRoom}
          onClose={() => setDeletingRoom(null)}
          onDeleted={() => {
            setDeletingRoom(null)
            refresh()
          }}
        />
      )}
    </div>
  )
}
