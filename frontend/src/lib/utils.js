export function probColor(prob, maxProb = 25) {
  if (prob == null) return 'var(--text-muted)'
  const t = Math.min(prob / maxProb, 1)
  const hue = Math.round(t * 120)
  return `hsl(${hue}, 70%, 55%)`
}
