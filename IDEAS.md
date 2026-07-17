# Ideas

## High impact, low effort

- **Pick timer** — countdown clock per pick (configurable seconds), auto-skips or flags if time runs out. Adds real pressure.
- **Undo last pick** — single-level undo, useful when someone fat-fingers a draft button.
- **Live odds refresh** — re-fetch odds mid-draft so late picks reflect market moves. Could show a delta (↑ / ↓) since draft start.
- **Best available highlight** — badge or pin on the highest-probability undrafted team so the current drafter has a clear anchor.

## Draft experience

- **Pre-draft wishlist** — before the draft starts, each player privately ranks/stars teams they want. Revealed after the draft for trash talk.
- **Pick grades** — on the finished page, score each pick by the odds at time of selection. Reward picking value, not just winners.
- **Draft recap email / export** — summary card per player: picks + odds at pick time + current odds. PDF or image.
- **Spectator mode** — shareable read-only URL so people not in the draft can watch the board update live.

## Setup

- **Save / load draft config** — persist player names, leagues, rounds to localStorage or a URL param so you don't re-enter every time.
- **Draft templates** — one-click presets like "NFL playoffs, 4 players, 3 rounds, Expert".
- **Multiple markets per league** — e.g. NBA Champion + NBA MVP as separate pools in the same draft.

## Social / fun

- **Trash talk log** — free-text comment box that appends to the draft board timeline. Exported with results.
- **Autopick** — if a player is away, randomly draft their highest-available pick. Flag it visually on the board.
- **Post-draft leaderboard** — after real events resolve, track who won based on drafted teams. Would need a results-entry flow.

## Stretch

- **Pauseable draft** — serialize full draft state to a shareable link so you can stop and resume across sessions.
- **Multiplayer / real-time** — each drafter on their own device, board updates live for everyone. Needs a backend (Supabase, Firebase, etc.).
