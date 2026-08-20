import { probColor } from '../lib/utils'

export function DraftedTeams({ teams }) {
  if (!teams.length) {
    return <p className="muted">No teams drafted yet.</p>
  }

  return (
    <div className="drafted-teams">
      {teams.map((team) => (
        <div className="drafted-team" key={`${team.roomId}-${team.teamId}`}>
          {team.logoUrl && <img src={team.logoUrl} alt="" className="drafted-team-logo" />}
          <div className="drafted-team-info">
            <span className="drafted-team-name">{team.displayName}</span>
            {team.leagueId && <span className="drafted-team-league">{team.leagueId.toUpperCase()}</span>}
          </div>
          {team.prob != null && (
            <span className="drafted-team-prob" style={{ color: probColor(team.prob) }}>
              {team.prob.toFixed(1)}%
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
