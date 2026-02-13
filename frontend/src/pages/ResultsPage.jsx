import { useLocation, useNavigate, Link } from 'react-router-dom';
import { MdSearch, MdReportProblem, MdCheckCircle, MdWarning } from 'react-icons/md';

function ResultsPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const result = location.state?.result;

    if (!result) {
        return (
            <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <p>No results to display. Go back and trace a number.</p>
                <div className="actions" style={{ marginTop: 20 }}>
                    <button className="btn-outline" onClick={() => navigate('/')}>
                        <MdSearch /> Search a Number
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="glass-card" style={{ animation: 'fadeIn 0.5s ease' }}>
                {/* Flag & Number */}
                <div className="result-flag">{result.flag}</div>
                <div className="result-number">{result.formatted_international}</div>

                {/* Validity */}
                <div style={{ textAlign: 'center', marginBottom: 20 }}>
                    {result.valid ? (
                        <span className="validity-badge valid">
                            <MdCheckCircle /> Valid Number
                        </span>
                    ) : (
                        <span className="validity-badge invalid">
                            <MdWarning /> Invalid / Not Active
                        </span>
                    )}
                </div>

                {/* Info Grid */}
                <div className="result-grid">
                    <div className="result-item">
                        <div className="label">Country</div>
                        <div className="value">{result.flag} {result.country_name}</div>
                    </div>
                    <div className="result-item">
                        <div className="label">Location</div>
                        <div className="value">{result.location || 'Unknown'}</div>
                    </div>
                    <div className="result-item">
                        <div className="label">Carrier</div>
                        <div className="value">{result.carrier || 'Unknown'}</div>
                    </div>
                    <div className="result-item">
                        <div className="label">Line Type</div>
                        <div className="value">{result.line_type || 'Unknown'}</div>
                    </div>
                    <div className="result-item">
                        <div className="label">Format (E.164)</div>
                        <div className="value" style={{ fontSize: '0.95rem' }}>{result.e164}</div>
                    </div>
                    <div className="result-item">
                        <div className="label">Timezone</div>
                        <div className="value" style={{ fontSize: '0.9rem' }}>
                            {result.timezones?.length > 0 ? result.timezones.join(', ') : 'Unknown'}
                        </div>
                    </div>
                </div>

                {/* Spam Reports */}
                <div className={`spam-section ${result.spam_reports === 0 ? 'clean' : ''}`}>
                    {result.spam_reports === 0 ? (
                        <>
                            <h3>🛡️ Clean Number</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                No spam or scam reports from the community.
                            </p>
                        </>
                    ) : (
                        <>
                            <h3>⚠️ {result.spam_reports} Spam Report{result.spam_reports > 1 ? 's' : ''}</h3>
                            <div style={{ marginTop: 8 }}>
                                {result.reports?.map((r, i) => (
                                    <div key={i} style={{ marginBottom: 8 }}>
                                        <span className="report-badge">{r.type}</span>
                                        {r.description && (
                                            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginLeft: 8 }}>
                                                {r.description}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                {/* Actions */}
                <div className="actions">
                    <button className="btn-outline" onClick={() => navigate('/')}>
                        <MdSearch /> Search Another
                    </button>
                    <Link
                        to="/report"
                        state={{ number: result.e164 }}
                        className="btn-accent"
                    >
                        <MdReportProblem /> Report This Number
                    </Link>
                </div>
            </div>

            <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </div>
    );
}

export default ResultsPage;
