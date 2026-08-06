



### ESPN API

In the ESPN API, the template URL for a league is:
```
http://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/seasons/{season}/
```

Based on this we map our available leagues through three columns: `espn_sport`, `espn_league` and `espn_season`

In Supabase, the `leagues` table is the one source of truth for playable leagues