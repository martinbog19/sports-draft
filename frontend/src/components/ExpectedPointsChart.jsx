import { useId, useMemo, useRef, useState } from 'react'

const WIDTH = 600
const HEIGHT = 160
const PADDING = 6

export function ExpectedPointsChart({ data, positive }) {
  const gradientId = useId()
  const svgRef = useRef(null)
  const [hover, setHover] = useState(null)

  const points = useMemo(() => {
    if (!data || data.length < 2) return []
    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1
    const stepX = (WIDTH - PADDING * 2) / (data.length - 1)
    return data.map((value, i) => ({
      x: PADDING + i * stepX,
      y: PADDING + (1 - (value - min) / range) * (HEIGHT - PADDING * 2),
      value,
    }))
  }, [data])

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ')
  const areaPath = points.length
    ? `${linePath} L${points[points.length - 1].x.toFixed(2)},${HEIGHT} L${points[0].x.toFixed(2)},${HEIGHT} Z`
    : ''

  const color = positive ? 'var(--success)' : 'var(--negative)'

  function handleMove(e) {
    if (!svgRef.current || points.length === 0) return
    const rect = svgRef.current.getBoundingClientRect()
    const relX = ((e.clientX - rect.left) / rect.width) * WIDTH
    const stepX = (WIDTH - PADDING * 2) / (points.length - 1)
    const index = Math.max(0, Math.min(points.length - 1, Math.round((relX - PADDING) / stepX)))
    setHover(points[index])
  }

  return (
    <div className="ep-chart-wrap">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        preserveAspectRatio="none"
        className="ep-chart"
        onMouseMove={handleMove}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {areaPath && <path d={areaPath} fill={`url(#${gradientId})`} stroke="none" />}
        {linePath && (
          <path d={linePath} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        )}
        {hover && (
          <>
            <line x1={hover.x} y1={0} x2={hover.x} y2={HEIGHT} stroke="var(--border)" strokeWidth="1" />
            <circle cx={hover.x} cy={hover.y} r="4.5" fill={color} stroke="var(--surface)" strokeWidth="2" />
          </>
        )}
      </svg>

      {hover && (
        <div
          className="ep-tooltip"
          style={{ left: `${Math.min(92, Math.max(8, (hover.x / WIDTH) * 100))}%` }}
        >
          {hover.value.toFixed(1)} pts
        </div>
      )}
    </div>
  )
}
