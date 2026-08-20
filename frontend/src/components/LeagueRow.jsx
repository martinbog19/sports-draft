export function LeagueRow({ room, playerCount, isHost, onEdit, onDelete, onLaunch, onOpen }) {
  const name = room.draft_name || room.code
  const status = room.status
  const nLeagues = (room.leagues || []).length

  return (
    <div className="league-row">
      <div className="league-row-main">
        <div className="league-row-top">
          <span className="league-row-name">{name}</span>
          <code className="league-row-code">{room.code}</code>
        </div>
        <p className="league-row-meta">
          {playerCount} player{playerCount !== 1 ? 's' : ''} · {nLeagues} league{nLeagues !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="league-row-actions">
        {isHost && status === 'lobby' && (
          <button className="link-btn" onClick={onEdit}>
            Edit
          </button>
        )}
        {isHost && (
          <button className="link-btn" onClick={onDelete}>
            Delete
          </button>
        )}
        {isHost && status === 'lobby' && (
          <button className="primary small" onClick={onLaunch}>
            Launch
          </button>
        )}
        {status === 'drafting' && (
          <button className="primary small" onClick={onOpen}>
            Open
          </button>
        )}
      </div>
    </div>
  )
}
