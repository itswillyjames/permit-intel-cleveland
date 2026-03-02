import React, { useEffect, useState } from 'react';
import axios from 'axios';

const Dashboard = () => {
  const [permits, setPermits] = useState([]);

  useEffect(() => {
    axios.get('/api/permits/')
      .then(res => setPermits(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h2>Permits</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Permit ID</th><th>City</th></tr>
        </thead>
        <tbody>
          {permits.map(p => (
            <tr key={p.id}>
              <td>{p.id}</td><td>{p.permit_id}</td><td>{p.city}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Dashboard;
