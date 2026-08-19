function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export function RoomCard({ room, playerCount, isHost, onEdit, onDelete, onLaunch, onOpen, onResults }) {
  const name = room.draft_name || room.code
  const status = room.status
  const snakeStr = room.snake ?? true ? 'Snake' : 'Linear'
  const roundsStr = `${room.rounds ?? '?'} rounds`
  const modeStr = room.mode || '—'
  const nLeagues = (room.leagues || []).length
  const leaguesStr = `${nLeagues} league${nLeagues !== 1 ? 's' : ''}`

  return (
    <div className="room-card">
      <div className="room-card-top">
        <span className="room-name">
          <strong>{name}</strong> <code>{room.code}</code>
        </span>
        {isHost && (
          <span className="room-card-actions">
            {status === 'lobby' && (
              <button className="link-btn" onClick={onEdit}>
                Edit
              </button>
            )}
            <button className="link-btn" onClick={onDelete}>
              🗑️
            </button>
          </span>
        )}
      </div>

      <p className="room-meta">{[modeStr, roundsStr, snakeStr, leaguesStr].join(' · ')}</p>
      <p className="room-meta">
        {formatDate(room.created_at)} · {playerCount} player{playerCount !== 1 ? 's' : ''}
      </p>

      <div className="room-card-bottom">
        <span className={`status-badge status-${status}`}>{status[0].toUpperCase() + status.slice(1)}</span>
        {isHost && status === 'lobby' && (
          <button className="primary small" onClick={onLaunch}>
            Launch draft!
          </button>
        )}
        {status === 'finished' && (
          <button className="primary small" onClick={onResults}>
            View results
          </button>
        )}
        {status === 'drafting' && (
          <button className="primary small" onClick={onOpen}>
            Open draft
          </button>
        )}
      </div>
    </div>
  )
}
