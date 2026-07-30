import { useState, useEffect } from 'react';

const EVENTS = [
  { ticker: 'KXPREMIERLEAGUE-27', label: 'Premier League' },
  { ticker: 'KXNHL-27', label: 'NHL' },
  { ticker: 'KXNBA-27', label: 'NBA' },
];

function App() {
  const [eventTicker, setEventTicker] = useState(EVENTS[0].ticker);
  const [refreshKey, setRefreshKey] = useState(0);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortDir, setSortDir] = useState('desc');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const url = `/kalshi-api/trade-api/v2/markets?event_ticker=${eventTicker}`;
      const response = await fetch(url);
      const json = await response.json();
      const markets = json.markets;

      // Equivalent of: data["price"] = (yes_ask + yes_bid) / 2
      const withPrice = markets.map((row) => ({
        ...row,
        price: (parseFloat(row.yes_ask_dollars) + parseFloat(row.yes_bid_dollars)) / 2,
      }));

      // Equivalent of: data["prob"] = 100 * price / price.sum()
      const totalPrice = withPrice.reduce((sum, row) => sum + row.price, 0);
      const withProb = withPrice.map((row) => ({
        ...row,
        prob: (100 * row.price) / totalPrice,
      }));

      setData(withProb);
      setLoading(false);
    };

    fetchData();
  }, [eventTicker, refreshKey]);

  const currentLabel = EVENTS.find((e) => e.ticker === eventTicker)?.label ?? eventTicker;

  const sortedData = [...data].sort((a, b) =>
    sortDir === 'asc' ? a.prob - b.prob : b.prob - a.prob
  );

  const toggleSort = () => setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0 }}>{currentLabel} Markets</h2>
        <select value={eventTicker} onChange={(e) => setEventTicker(e.target.value)}>
          {EVENTS.map((event) => (
            <option key={event.ticker} value={event.ticker}>
              {event.label}
            </option>
          ))}
        </select>
        <button onClick={() => setRefreshKey((k) => k + 1)} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      {loading ? (
        <p>Loading...</p>
      ) : (
      <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Sub Title</th>
            <th>Price</th>
            <th onClick={toggleSort} style={{ cursor: 'pointer', userSelect: 'none' }}>
              Prob (%) {sortDir === 'asc' ? '▲' : '▼'}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, i) => (
            <tr key={i}>
              <td>{row.yes_sub_title}</td>
              <td>{row.price.toFixed(2)}</td>
              <td>{row.prob.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      )}
    </div>
  );
}

export default App;