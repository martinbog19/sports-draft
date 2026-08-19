import { useEffect, useState } from 'react'
import { Modal } from './Modal'
import { PillGroup } from './PillGroup'
import { getLeagues, updateRoom } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function EditRoomModal({ room, onClose, onSaved }) {
  const { user } = useAuth()
  const currentLeagues = room.leagues || []

  const [snake, setSnake] = useState(room.snake ?? true)
  const [rounds, setRounds] = useState(room.rounds ?? 25)
  const [mode, setMode] = useState(room.mode ?? null)
  const [oddsProvider, setOddsProvider] = useState(room.odds_provider ?? 'Polymarket')
  const [leagues, setLeagues] = useState([])
  const [selectedLeagues, setSelectedLeagues] = useState(currentLeagues)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getLeagues()
      .then((res) => setLeagues(res.leagues || []))
      .catch(() => setLeagues([]))
  }, [])

  function toggleLeague(id) {
    setSelectedLeagues((prev) =>
      prev.includes(id) ? prev.filter((l) => l !== id) : [...prev, id]
    )
  }

  const changed =
    snake !== (room.snake ?? true) ||
    rounds !== (room.rounds ?? 25) ||
    mode !== room.mode ||
    oddsProvider !== room.odds_provider ||
    JSON.stringify([...selectedLeagues].sort()) !== JSON.stringify([...currentLeagues].sort())

  async function handleSave() {
    setBusy(true)
    setError('')
    try {
      await updateRoom(room.code, user.id, {
        snake,
        rounds,
        mode,
        odds_provider: mode !== 'Expert' ? oddsProvider : null,
        leagues: selectedLeagues,
      })
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Edit draft" onClose={onClose}>
      <div className="edit-form">
        <div className="edit-row">
          <label className="toggle-label">
            <input type="checkbox" checked={snake} onChange={(e) => setSnake(e.target.checked)} />
            Snake draft
          </label>
          <label>
            Rounds
            <input
              type="number"
              min={1}
              max={100}
              value={rounds}
              onChange={(e) => setRounds(Number(e.target.value))}
            />
          </label>
        </div>

        <label>
          Game mode
          <PillGroup options={['Easy', 'Blurred', 'Expert']} value={mode} onChange={setMode} />
        </label>

        {mode && mode !== 'Expert' && (
          <label>
            Odds provider
            <PillGroup options={['Kalshi', 'Polymarket']} value={oddsProvider} onChange={setOddsProvider} />
          </label>
        )}

        <label>Leagues</label>
        <div className="league-list">
          {leagues.map((league) => (
            <label key={league.id} className="toggle-label">
              <input
                type="checkbox"
                checked={selectedLeagues.includes(league.id)}
                onChange={() => toggleLeague(league.id)}
              />
              {league.display_name}
            </label>
          ))}
        </div>

        {error && <p className="error">{error}</p>}
        <button
          className="primary"
          disabled={!changed || selectedLeagues.length === 0 || busy}
          onClick={handleSave}
        >
          {busy ? 'Saving…' : 'Save'}
        </button>
      </div>
    </Modal>
  )
}
