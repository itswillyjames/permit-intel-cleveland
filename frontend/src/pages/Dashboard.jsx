import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './Dashboard.css';

function Dashboard() {
  const [permits, setPermits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('permits');

  useEffect(() => {
    fetchPermits();
  }, []);

  const fetchPermits = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/permits/');
      setPermits(response.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runPipeline = async () => {
    try {
      setLoading(true);
      // Stub: trigger backend pipeline
      alert('Pipeline triggered! Check logs.');
      fetchPermits();
    } catch (err) {
      setError('Failed to run pipeline: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🎯 Permit Arbitrage Intelligence Hub</h1>
        <button onClick={runPipeline} disabled={loading}>
          {loading ? 'Running...' : 'Run Pipeline'}
        </button>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'permits' ? 'active' : ''}
          onClick={() => setActiveTab('permits')}
        >
          Permits
        </button>
        <button
          className={activeTab === 'packages' ? 'active' : ''}
          onClick={() => setActiveTab('packages')}
        >
          Packages
        </button>
        <button
          className={activeTab === 'sources' ? 'active' : ''}
          onClick={() => setActiveTab('sources')}
        >
          Sources
        </button>
      </nav>

      {error && <div className="error">{error}</div>}

      {activeTab === 'permits' && (
        <div className="permits-table">
          <h2>Permits ({permits.length})</h2>
          {loading ? (
            <p>Loading...</p>
          ) : permits.length === 0 ? (
            <p>No permits loaded. Run pipeline to fetch data.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>City</th>
                  <th>Address</th>
                  <th>Type</th>
                  <th>Valuation</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {permits.map((p) => (
                  <tr key={p.id}>
                    <td>{p.permit_id}</td>
                    <td>{p.city}</td>
                    <td>{p.address}</td>
                    <td>{p.permit_type}</td>
                    <td>${p.valuation?.toLocaleString() || 'N/A'}</td>
                    <td>{p.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'packages' && (
        <div className="packages-section">
          <h2>Curated Packages</h2>
          <p>Multi-vertical packages coming soon...</p>
        </div>
      )}

      {activeTab === 'sources' && (
        <div className="sources-section">
          <h2>Data Sources</h2>
          <p>Configure sources for new cities...</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
