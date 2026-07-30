import { useState, useEffect } from 'react';

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const eventTicker = 'KXPREMIERLEAGUE-27'; // .upper().strip() done manually here
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
  }, []);

  if (loading) return <p style={{ padding: '2rem' }}>Loading...</p>;

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h2>Premier League Markets</h2>
      <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Sub Title</th>
            <th>Price</th>
            <th>Prob (%)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              <td>{row.yes_sub_title}</td>
              <td>{row.price.toFixed(2)}</td>
              <td>{row.prob.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;