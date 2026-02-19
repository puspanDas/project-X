import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useState } from 'react';
import { MdSearch, MdReportProblem, MdCheckCircle, MdWarning, MdAutoAwesome } from 'react-icons/md';
import { analyzeNumber } from '../api';

function ResultsPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const result = location.state?.result;
    const [aiResult, setAiResult] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);
    const [aiError, setAiError] = useState('');

    const handleAIAnalysis = async () => {
        if (aiLoading || aiResult) return;
        setAiLoading(true);
        setAiError('');
        try {
            const analysis = await analyzeNumber(result);
            setAiResult(analysis);
        } catch (err) {
            setAiError('Failed to run AI analysis. Is the backend running?');
        } finally {
            setAiLoading(false);
        }
    };

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

    const getRiskColor = (level) => {
        switch (level) {
            case 'Critical': return '#ff4757';
            case 'High': return '#ff6b6b';
            case 'Medium': return '#ff9f43';
            case 'Low': return '#00d4aa';
            default: return '#8888a8';
        }
    };

    const getRiskGradient = (score) => {
        if (score >= 70) return 'linear-gradient(90deg, #ff4757, #ff6b6b)';
        if (score >= 45) return 'linear-gradient(90deg, #ff6b6b, #ff9f43)';
        if (score >= 25) return 'linear-gradient(90deg, #ff9f43, #ffd32a)';
        return 'linear-gradient(90deg, #00d4aa, #6c63ff)';
    };

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
                        <div className="label">
                            Carrier
                            {result.carrier_source === 'live' && (
                                <span style={{ marginLeft: 8, fontSize: '0.65rem', padding: '2px 8px', background: 'rgba(0,212,170,0.15)', color: 'var(--accent-secondary)', borderRadius: 100, fontWeight: 600 }}>LIVE</span>
                            )}
                            {result.carrier_source === 'offline' && (
                                <span style={{ marginLeft: 8, fontSize: '0.65rem', padding: '2px 8px', background: 'rgba(255,159,67,0.15)', color: 'var(--accent-orange)', borderRadius: 100, fontWeight: 600 }}>OFFLINE</span>
                            )}
                        </div>
                        <div className="value">{result.carrier || 'Unknown'}</div>
                        {result.original_carrier && result.original_carrier !== result.carrier && (
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                                Originally: {result.original_carrier}
                            </div>
                        )}
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

                {/* Carrier accuracy note */}
                {result.carrier_source === 'offline' && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: 12, fontStyle: 'italic' }}>
                        ⓘ Carrier shown is based on original number allocation. If ported (MNP), actual carrier may differ.
                    </div>
                )}

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

                {/* === AI ANALYSIS SECTION === */}
                {!aiResult && !aiLoading && (
                    <div style={{ textAlign: 'center', marginTop: 24 }}>
                        <button
                            className="ai-analyze-btn"
                            onClick={handleAIAnalysis}
                            disabled={aiLoading}
                        >
                            <MdAutoAwesome style={{ fontSize: '1.2rem' }} />
                            <span>Run AI Threat Analysis</span>
                            <span className="ai-analyze-badge">AI</span>
                        </button>
                    </div>
                )}

                {aiLoading && (
                    <div className="ai-analysis-loading">
                        <div className="ai-pulse-ring"></div>
                        <p>Analyzing threat indicators...</p>
                    </div>
                )}

                {aiError && (
                    <div className="error-message" style={{ marginTop: 20 }}>{aiError}</div>
                )}

                {aiResult && (
                    <div className="ai-analysis-card" style={{ animation: 'fadeIn 0.5s ease' }}>
                        <div className="ai-analysis-header">
                            <MdAutoAwesome style={{ color: 'var(--accent-primary)', fontSize: '1.3rem' }} />
                            <span>AI Threat Analysis</span>
                            <span className="ai-badge-glow">AI</span>
                            {aiResult.ai_source === 'llm' && (
                                <span style={{
                                    fontSize: '0.6rem', padding: '2px 8px',
                                    background: 'rgba(0, 212, 170, 0.15)', color: '#00d4aa',
                                    borderRadius: '100px', fontWeight: 700, letterSpacing: '0.5px',
                                    border: '1px solid rgba(0, 212, 170, 0.2)',
                                }}>LLM</span>
                            )}
                        </div>

                        {/* Risk Meter */}
                        <div className="ai-risk-meter">
                            <div className="ai-risk-labels">
                                <span>Risk Score</span>
                                <span style={{ color: getRiskColor(aiResult.risk_level), fontWeight: 700, fontSize: '1.5rem' }}>
                                    {aiResult.risk_score}
                                    <span style={{ fontSize: '0.9rem', opacity: 0.7 }}>/100</span>
                                </span>
                            </div>
                            <div className="ai-risk-bar-bg">
                                <div
                                    className="ai-risk-bar-fill"
                                    style={{
                                        width: `${aiResult.risk_score}%`,
                                        background: getRiskGradient(aiResult.risk_score),
                                    }}
                                ></div>
                            </div>
                        </div>

                        {/* Risk Level & Threat Type */}
                        <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                            <span className="ai-risk-badge" style={{ background: getRiskColor(aiResult.risk_level) + '22', color: getRiskColor(aiResult.risk_level), borderColor: getRiskColor(aiResult.risk_level) + '33' }}>
                                {aiResult.risk_level} Risk
                            </span>
                            <span className="ai-threat-badge">
                                {aiResult.threat_type}
                            </span>
                        </div>

                        {/* Analysis Text */}
                        <div className="ai-analysis-text">
                            {aiResult.analysis}
                        </div>

                        {/* Factors */}
                        {aiResult.factors && aiResult.factors.length > 0 && (
                            <div className="ai-factors">
                                <div className="ai-factors-title">Risk Factors</div>
                                {aiResult.factors.map((f, i) => (
                                    <div key={i} className="ai-factor-item">
                                        <span className="ai-factor-dot"></span>
                                        {f}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Recommendation */}
                        <div className="ai-recommendation">
                            {aiResult.recommendation}
                        </div>
                    </div>
                )}

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
