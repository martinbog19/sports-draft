import { Link } from 'react-router-dom'

export default function ComingSoon({ title }) {
  return (
    <div className="home-page">
      <h2>{title}</h2>
      <p className="muted">Not built yet — coming in the next phase.</p>
      <Link to="/home">← Back home</Link>
    </div>
  )
}
