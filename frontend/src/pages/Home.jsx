import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { listRooms, getRoomPlayers, getRoom, startDraft } from '../lib/api'
import { LeagueRow } from '../components/LeagueRow'
import { ExpectedPointsChart } from '../components/ExpectedPointsChart'
import { DraftedTeams } from '../components/DraftedTeams'
import { Skeleton } from '../components/Skeleton'
import { JoinRoomModal } from '../components/JoinRoomModal'
import { EditRoomModal } from '../components/EditRoomModal'
import { DeleteRoomModal } from '../components/DeleteRoomModal'
import './Home.css'

const RANGES = ['1D', '1W', '1M', 'ALL']
const STATUS_GROUPS = [
  { key: 'lobby', label: 'Lobby' },
  { key: 'drafting', label: 'Drafting' },
]

function seededRandom(seed) {
  let h = 0
  for (let i = 0; i < seed.length; i++) h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0
  return () => {
    h = Math.imul(h ^ (h >>> 15), h | 1)
    h ^= h + Math.imul(h ^ (h >>> 7), h | 61)
    return ((h ^ (h >>> 14)) >>> 0) / 4294967296
  }
}

// Placeholder series — swapped for real historical probability tracking later.
function mockSeries(seedKey, range) {
  const lengths = { '1D': 24, '1W': 42, '1M': 30, ALL: 90 }
  const n = lengths[range] ?? 30
  const rand = seededRandom(`${seedKey}-${range}`)
  let value = 100
  const series = [value]
  for (let i = 1; i < n; i++) {
    value += (Math.sin(i / 4) + (rand() - 0.5)) * 2.5
    series.push(value)
  }
  return series
}

export default function Home() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const [rooms, setRooms] = useState([])
  const [playerCounts, setPlayerCounts] = useState({})
  const [draftedByRoom, setDraftedByRoom] = useState({})
  const [loadError, setLoadError] = useState('')
  const [loading, setLoading] = useState(true)

  const [showJoin, setShowJoin] = useState(false)
  const [editingRoom, setEditingRoom] = useState(null)
  const [deletingRoom, setDeletingRoom] = useState(null)
  const [launchError, setLaunchError] = useState('')

  const [range, setRange] = useState('1D')
  const [view, setView] = useState('all')
  const series = useMemo(() => mockSeries(view, range), [view, range])
  const current = series[series.length - 1]
  const delta = current - series[0]
  const deltaPct = series[0] !== 0 ? (delta / series[0]) * 100 : 0
  const positive = delta >= 0

  const refresh = useCallback(async () => {
    try {
      const { rooms: data } = await listRooms(user.id)
      const sorted = [...data].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
      setRooms(sorted)

      const counts = {}
      const drafted = {}
      await Promise.all(
        sorted.map(async (room) => {
          const { players } = await getRoomPlayers(room.code)
          counts[room.code] = players.length

          if (room.status !== 'lobby') {
            const { picks, pool } = await getRoom(room.id)
            const poolByTeam = Object.fromEntries(pool.map((t) => [t.team_id, t]))
            drafted[room.id] = picks
              .filter((p) => p.user_id === user.id)
              .map((p) => {
                const team = poolByTeam[p.team] || {}
                return {
                  roomId: room.id,
                  teamId: p.team,
                  displayName: team.display_name || p.team,
                  logoUrl: team.logo_url,
                  leagueId: team.league_id || p.league,
                  prob: team.prob ?? null,
                }
              })
          }
        })
      )
      setPlayerCounts(counts)
      setDraftedByRoom(drafted)
      setLoadError('')
    } catch (err) {
      setLoadError(`Could not load leagues — make sure the backend is running. [${err.message}]`)
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

  const grouped = useMemo(() => {
    const groups = { lobby: [], drafting: [], finished: [] }
    for (const room of rooms) {
      const key = (room.status || 'lobby').toLowerCase()
      if (groups[key]) groups[key].push(room)
    }
    return groups
  }, [rooms])

  const draftedTeams = useMemo(() => {
    if (view === 'all') return Object.values(draftedByRoom).flat()
    return draftedByRoom[view] || []
  }, [draftedByRoom, view])

  const viewOptions = useMemo(
    () => [
      { value: 'all', label: 'All Leagues' },
      ...grouped.finished.map((room) => ({ value: room.id, label: room.draft_name || room.code })),
    ],
    [grouped.finished]
  )

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

      {launchError && <p className="error">{launchError}</p>}

      <div className="dashboard-grid">
        <section className="panel points-panel">
          <div className="points-header">
            <h3>Expected Points</h3>
            <select className="view-select" value={view} onChange={(e) => setView(e.target.value)}>
              {viewOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {view !== 'all' && (
            <button className="link-btn view-results-link" onClick={() => navigate('/results', { state: { roomId: view } })}>
              View full draft →
            </button>
          )}

          <div className="points-value-row">
            <span className="points-value">{current.toFixed(1)} pts</span>
            <span className={`points-delta ${positive ? 'positive' : 'negative'}`}>
              {positive ? '▲' : '▼'} {Math.abs(delta).toFixed(1)} ({Math.abs(deltaPct).toFixed(1)}%)
            </span>
          </div>

          <ExpectedPointsChart data={series} positive={positive} />

          <div className="range-toggle">
            {RANGES.map((r) => (
              <button
                key={r}
                className={`range-btn ${range === r ? 'active' : ''}`}
                onClick={() => setRange(r)}
              >
                {r}
              </button>
            ))}
          </div>

          <p className="points-note">Placeholder data — live probability tracking is coming soon.</p>

          <div className="drafted-section">
            <span className="drafted-section-label">My Drafted Teams</span>
            {loading ? (
              <div className="drafted-teams">
                {[0, 1, 2, 3].map((i) => (
                  <Skeleton key={i} width="112px" height="40px" radius={10} />
                ))}
              </div>
            ) : (
              <DraftedTeams teams={draftedTeams} />
            )}
          </div>
        </section>

        <section className="panel leagues-panel">
          <h3>My Leagues</h3>

          <div className="leagues-actions">
            <button className="primary" onClick={() => navigate('/start')}>
              + Create
            </button>
            <button className="secondary" onClick={() => setShowJoin(true)}>
              Enter a code
            </button>
          </div>

          {loading && (
            <div className="league-groups">
              <div className="league-group">
                {[0, 1, 2].map((i) => (
                  <div className="league-row" key={i}>
                    <div className="league-row-main">
                      <Skeleton width="55%" height="14px" />
                      <Skeleton width="35%" height="11px" style={{ marginTop: 6 }} />
                    </div>
                    <Skeleton width="64px" height="30px" radius={8} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && loadError && <p className="warning-text">{loadError}</p>}
          {!loading && !loadError && rooms.length === 0 && (
            <p className="muted">No leagues yet. Create one or join with a code.</p>
          )}

          {!loading && !loadError && (
            <div className="league-groups">
              {STATUS_GROUPS.map(
                ({ key, label }) =>
                  grouped[key].length > 0 && (
                    <div className="league-group" key={key}>
                      <span className="league-group-label">{label}</span>
                      {grouped[key].map((room) => (
                        <LeagueRow
                          key={room.id}
                          room={room}
                          playerCount={playerCounts[room.code] ?? 0}
                          isHost={room.host_id === user.id}
                          onEdit={() => setEditingRoom(room)}
                          onDelete={() => setDeletingRoom(room)}
                          onLaunch={() => handleLaunch(room)}
                          onOpen={() => navigate('/draft', { state: { room } })}
                        />
                      ))}
                    </div>
                  )
              )}
            </div>
          )}
        </section>
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
