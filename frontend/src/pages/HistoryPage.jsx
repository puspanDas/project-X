import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MdHistory, MdRefresh } from 'react-icons/md';
import { getHistory, traceNumber } from '../api';

function HistoryPage() {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const data = await getHistory();
            setHistory(data);
        } catch (err) {
            console.error('Failed to load history', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const handleClick = async (number) => {
        try {
            const result = await traceNumber(number);
            navigate('/results', { state: { result } });
        } catch (err) {
            console.error('Re-trace failed', err);
        }
    };

    const formatTime = (iso) => {
        try {
            const d = new Date(iso);
            return d.toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });
        } catch {
            return '';
        }
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <div className="spinner"></div>
                <div className="loading-text">Loading history...</div>
            </div>
        );
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <h1 className="page-title" style={{ marginBottom: 0 }}>
                    <MdHistory className="icon" style={{ color: 'var(--accent-primary)' }} />
                    Recent Lookups
                </h1>
                <button className="btn-outline" onClick={fetchHistory} style={{ padding: '8px 16px' }}>
                    <MdRefresh /> Refresh
                </button>
            </div>

            {history.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📋</div>
                    <p>No lookups yet. Trace a number to get started!</p>
                </div>
            ) : (
                <div className="history-list">
                    {history.map((item, i) => (
                        <div
                            key={i}
                            className="history-item"
                            onClick={() => handleClick(item.number)}
                            style={{ animationDelay: `${i * 0.05}s` }}
                        >
                            <div className="history-flag">{item.flag || '🌍'}</div>
                            <div className="history-info">
                                <div className="history-number">{item.formatted || item.number}</div>
                                <div className="history-meta">
                                    {item.country} · {item.line_type} · {item.location}
                                </div>
                            </div>
                            <div className="history-carrier">{item.carrier}</div>
                            <div className="history-time">{formatTime(item.timestamp)}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default HistoryPage;
