import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { getRoom } from '../lib/api'
import { probColor } from '../lib/utils'
import './Results.css'

export default function Results() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const roomId = state?.roomId

  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!roomId) return
    getRoom(roomId)
      .then(setData)
      .catch((err) => setError(err.message))
  }, [roomId])

  const groups = useMemo(() => {
    if (!data) return []
    const { picks, pool, players } = data
    const playerByUser = Object.fromEntries(players.map((p) => [p.user_id, p]))
    const poolByTeam = Object.fromEntries(pool.map((t) => [t.team_id, t]))

    const byLeague = {}
    for (const pick of picks) {
      const team = poolByTeam[pick.team] || {}
      const leagueId = team.league_id || pick.league || 'unknown'
      if (!byLeague[leagueId]) byLeague[leagueId] = []
      byLeague[leagueId].push({
        id: pick.id ?? `${pick.team}-${pick.pick_number}`,
        teamName: team.display_name || pick.team,
        logoUrl: team.logo_url,
        prob: team.prob ?? null,
        drafterName: playerByUser[pick.user_id]?.display_name || pick.display_name,
        round: pick.round,
        pickNumber: pick.pick_number,
      })
    }

    for (const list of Object.values(byLeague)) {
      list.sort((a, b) => {
        if (a.prob == null && b.prob == null) return a.pickNumber - b.pickNumber
        if (a.prob == null) return 1
        if (b.prob == null) return -1
        return b.prob - a.prob
      })
    }

    return Object.entries(byLeague).sort(([a], [b]) => a.localeCompare(b))
  }, [data])

  return (
    <div className="results-page">
      <header className="results-header">
        <button className="secondary" onClick={() => navigate('/home')}>
          ← Back
        </button>
        {data && <h2>{data.room.draft_name || data.room.code}</h2>}
      </header>

      {!roomId && <p className="muted">No draft selected.</p>}
      {error && <p className="warning-text">{error}</p>}
      {roomId && !data && !error && <p className="muted">Loading…</p>}

      {data && (
        <div className="results-groups">
          {groups.map(([leagueId, picks]) => (
            <section className="panel results-group" key={leagueId}>
              <span className="results-group-label">{leagueId.toUpperCase()}</span>
              <div className="results-picks">
                {picks.map((pick) => (
                  <div className="results-pick" key={pick.id}>
                    {pick.logoUrl && <img src={pick.logoUrl} alt="" className="results-pick-logo" />}
                    <div className="results-pick-info">
                      <span className="results-pick-team">{pick.teamName}</span>
                      <span className="results-pick-drafter">{pick.drafterName}</span>
                      <span className="results-pick-round">
                        Rd {pick.round} · Pick #{pick.pickNumber}
                      </span>
                    </div>
                    {pick.prob != null && (
                      <span className="results-pick-prob" style={{ color: probColor(pick.prob) }}>
                        {pick.prob.toFixed(1)}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
