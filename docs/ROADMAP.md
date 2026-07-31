# From Streamlit Prototype to iOS App — Roadmap

## The core problem to solve first

Before touching mobile, the app needs a **real backend**. Right now all state lives in a single browser session — there's no persistence, no multiplayer, no accounts. The jump from Streamlit to iOS is really two separate jumps: (1) prototype → real backend, (2) web → mobile. Do them in order.

---

## Technologies involved

**Languages**
- Python — backend (FastAPI)
- JavaScript / TypeScript — web frontend (React) + mobile (React Native)
- SQL — querying/structuring the Supabase database

**Backend**
- FastAPI — your API server
- Supabase — database, auth, realtime (hosted, no setup)

**Frontend / Mobile**
- React — web app
- React Native + Expo — iOS/Android app

**Infrastructure**
- Supabase — hosts your database and realtime layer
- Railway / Render / Fly.io — hosts your FastAPI server (simple, cheap, Python-friendly)
- Apple Developer Program — required to ship to App Store

**Tooling**
- Git — version control (already using this)
- Xcode — required on Mac to build iOS apps (free, just large)
- EAS (Expo Application Services) — builds and submits your app to the App Store without needing to touch Xcode much

**External APIs**
- Polymarket / Kalshi — odds data (already integrated)

The only genuinely new things compared to what you already do are **JavaScript/TypeScript** and **SQL**. SQL is simple and you'll pick it up in a day. JS is the real investment, but once you know it React and React Native follow naturally.

---

## Stack recommendation

Given your Python background, the goal is to minimize the number of new languages you need to learn deeply.

| Layer | Choice | Why |
|---|---|---|
| Backend | **FastAPI** + **PostgreSQL** | Pure Python, async, you already know this world |
| Realtime | **Supabase** | Managed Postgres + built-in WebSocket pub/sub + Auth + hosted — replaces 4 services at once |
| Mobile | **React Native (Expo)** | Cross-platform (iOS + Android), JS is learnable, huge ecosystem |
| Odds data | Keep Kalshi/Polymarket | Already working, just move it server-side |

**Why not Swift/native iOS?** Steep learning curve, iOS-only, longer release cycles. You'd spend 80% of your time learning platform APIs instead of building product.

**Why not Flutter?** Dart is a fine language but has a smaller ecosystem. React Native has more third-party libraries and more Stack Overflow answers, which matters when you're learning.

**Why Supabase over rolling your own?** Auth, real-time, storage, and Postgres in one hosted service. You can spend weeks building auth from scratch or get it done in a day. Start with Supabase, self-host later if you ever need to.

---

## Phase 1 — Real backend (4–6 weeks)

The goal: make the current app work for two people on different computers.

### What to build
- **User auth** — sign up / log in (Supabase Auth handles this out of the box)
- **Draft rooms** — create a room, get an invite code, friends join with the code
- **Persistent game state** — rounds, picks, players, settings stored in Postgres, not browser memory
- **Real-time sync** — when one player drafts, everyone else's board updates instantly (Supabase Realtime or FastAPI WebSockets)
- **Odds fetching moved server-side** — one server fetches from Kalshi/Polymarket at draft start, stores in DB, serves to all clients. No more each browser calling the API directly.

### Data model (simplified)
```
users         — id, email, display_name
rooms         — id, code, host_id, settings (snake, rounds, mode, leagues), status
room_players  — room_id, user_id, seat_order
picks         — room_id, round, position, user_id, team, league, prob_at_pick_time
pool          — room_id, team, league, prob (snapshot at draft start)
```

### Keep the Streamlit UI for now
Use Streamlit as the frontend for Phase 1. It's ugly for multiplayer but it lets you validate the backend without learning React yet. Wire Streamlit to call your FastAPI endpoints instead of computing state locally.

**Milestone:** two people on different laptops completing a draft together.

---

## Phase 2 — Web frontend (4–6 weeks)

Replace Streamlit with a proper web app. This is your bridge to mobile — React Native shares almost all its concepts with React.

### Why not skip straight to mobile?
Web is faster to iterate on, easier to debug, and gives you something shareable without App Store approval. Build the web version first, then port it to React Native — you'll reuse 60–70% of the logic.

### What to build
- **React + Vite** (or **Next.js** if you want server-side rendering later)
- Replicate the three screens: Setup, Draft Room, Finished
- Real-time board updates via Supabase Realtime client
- Mobile-responsive layout — if it works well on a phone browser, porting to React Native is mostly cosmetic

### Learning path for React
If you've never written JavaScript: spend one week on JS fundamentals (MDN), then go straight to the official React tutorial. You don't need to master JS — you need to be functional. Your Python intuition transfers well (functions, state, loops — same concepts, different syntax).

**Milestone:** fully working web app, shareable link, playable on phone browser.

---

## Phase 3 — iOS app with React Native (6–8 weeks)

Now you port the web app to mobile.

### Why React Native is the right move here
- You write JavaScript/TypeScript (already learned in Phase 2)
- **Expo** abstracts away most of the iOS/Android build complexity
- Core components (`View`, `Text`, `FlatList`, `TouchableOpacity`) map almost directly to HTML elements you used in React
- The backend, API calls, and Supabase client code are **identical** — you're really just rewriting the UI layer

### What changes from web to mobile
- No CSS — use `StyleSheet` objects (similar concept, different syntax)
- Navigation between screens: use **React Navigation** (replaces URL routing)
- No browser APIs — use Expo's libraries for things like notifications, haptics, share sheet
- Layout: Flexbox is actually more consistent in React Native than on the web

### Key mobile features to add
- **Push notifications** — "it's your pick" alert when it's a player's turn (Expo Notifications)
- **Haptic feedback** — subtle tap on draft button
- **Deep links** — tap an invite link to open the app directly in the right room
- **Offline resilience** — handle spotty connections gracefully (retry logic on picks)

### App Store submission
- You'll need an **Apple Developer account** ($99/year)
- Expo can build the `.ipa` for you with `eas build`
- First review takes 1–3 days; updates are faster
- TestFlight lets you share beta builds with friends before going public — use this heavily

**Milestone:** TestFlight build your friend can install and play a real draft with you.

---

## Phase 4 — Polish & growth (ongoing)

Once the core loop works on mobile:

- **Post-draft tracking** — after real events resolve, who won? Requires storing picks permanently and a results-entry flow or automated resolution via Kalshi/Polymarket settlement APIs
- **Push notification pick timer** — "you have 60 seconds" with a badge count
- **Season-long leagues** — same group of friends, multiple drafts, cumulative leaderboard
- **Social layer** — draft history, head-to-head records, trash talk threads
- **Monetization** — if you ever want to go there: premium leagues, more markets, cosmetics

---

## Honest timeline

| Phase | Estimated time | Gating skill to learn |
|---|---|---|
| 1 — Backend | 4–6 weeks | FastAPI + SQL (you're close already) |
| 2 — Web frontend | 4–6 weeks | React + JavaScript |
| 3 — React Native | 6–8 weeks | React Native + Expo toolchain |
| 4 — App Store + polish | 2–4 weeks | Xcode basics, EAS Build |

**Realistic total: 4–6 months** to a TestFlight beta, working nights/weekends. The biggest time sink won't be coding — it'll be debugging the React Native build pipeline and the App Store review process.

---

## What to do this week

1. Create a Supabase project (free tier is enough)
2. Define the DB schema for rooms and picks
3. Write a FastAPI endpoint that creates a room and returns an invite code
4. Wire the Streamlit app to call that endpoint instead of using session state

That first endpoint is the proof that the architecture works. Everything else follows from it.
