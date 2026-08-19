const BASE = import.meta.env.VITE_BACKEND_URL

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || `Request failed: ${res.status}`)
  }
  return data
}

export function listRooms(userId) {
  return request(`/rooms?user_id=${encodeURIComponent(userId)}`)
}

export function getRoomPlayers(code) {
  return request(`/rooms/${code}/players`)
}

export function joinRoom(userId, code, displayName) {
  return request(`/rooms/${code}/join`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, display_name: displayName }),
  })
}

export function updateRoom(code, userId, updates) {
  return request(`/rooms/${code}`, {
    method: 'PUT',
    body: JSON.stringify({ user_id: userId, ...updates }),
  })
}

export function deleteRoom(code, userId) {
  return request(`/rooms/${code}?user_id=${encodeURIComponent(userId)}`, {
    method: 'DELETE',
  })
}

export function startDraft(code, userId) {
  return request(`/rooms/${code}/start`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  })
}

export function getLeagues() {
  return request('/leagues')
}
