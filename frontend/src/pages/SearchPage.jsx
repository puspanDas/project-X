import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LuMapPin } from 'react-icons/lu';
import { traceNumber } from '../api';

const COUNTRY_CODES = [
    { code: '+1', label: '🇺🇸 +1' },
    { code: '+44', label: '🇬🇧 +44' },
    { code: '+91', label: '🇮🇳 +91' },
    { code: '+61', label: '🇦🇺 +61' },
    { code: '+49', label: '🇩🇪 +49' },
    { code: '+33', label: '🇫🇷 +33' },
    { code: '+81', label: '🇯🇵 +81' },
    { code: '+86', label: '🇨🇳 +86' },
    { code: '+55', label: '🇧🇷 +55' },
    { code: '+7', label: '🇷🇺 +7' },
    { code: '+971', label: '🇦🇪 +971' },
    { code: '+966', label: '🇸🇦 +966' },
    { code: '+234', label: '🇳🇬 +234' },
    { code: '+27', label: '🇿🇦 +27' },
    { code: '+82', label: '🇰🇷 +82' },
    { code: '+39', label: '🇮🇹 +39' },
    { code: '+34', label: '🇪🇸 +34' },
    { code: '+52', label: '🇲🇽 +52' },
    { code: '+62', label: '🇮🇩 +62' },
    { code: '+90', label: '🇹🇷 +90' },
    { code: '+48', label: '🇵🇱 +48' },
    { code: '+31', label: '🇳🇱 +31' },
    { code: '+46', label: '🇸🇪 +46' },
    { code: '+41', label: '🇨🇭 +41' },
    { code: '+63', label: '🇵🇭 +63' },
    { code: '+66', label: '🇹🇭 +66' },
    { code: '+84', label: '🇻🇳 +84' },
    { code: '+92', label: '🇵🇰 +92' },
    { code: '+880', label: '🇧🇩 +880' },
    { code: '+20', label: '🇪🇬 +20' },
    { code: '+254', label: '🇰🇪 +254' },
    { code: '+233', label: '🇬🇭 +233' },
];

function SearchPage() {
    const [countryCode, setCountryCode] = useState('+91');
    const [phone, setPhone] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleTrace = async (e) => {
        e.preventDefault();
        if (!phone.trim()) return;

        setLoading(true);
        setError('');

        try {
            const fullNumber = countryCode + phone.replace(/\s/g, '');
            const result = await traceNumber(fullNumber);
            navigate('/results', { state: { result } });
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to trace number. Please check the format and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div className="hero">
                <h1>🔍 Phone Tracer</h1>
                <p>Trace any unknown phone number worldwide. Get carrier info, location, line type, and community spam reports.</p>
            </div>

            <form className="search-box" onSubmit={handleTrace}>
                <div className="search-input-group">
                    <select
                        className="country-select"
                        value={countryCode}
                        onChange={e => setCountryCode(e.target.value)}
                    >
                        {COUNTRY_CODES.map(c => (
                            <option key={c.code} value={c.code}>{c.label}</option>
                        ))}
                    </select>
                    <input
                        className="phone-input"
                        type="tel"
                        placeholder="Enter phone number..."
                        value={phone}
                        onChange={e => setPhone(e.target.value)}
                        autoFocus
                    />
                    <button className="trace-btn" type="submit" disabled={loading || !phone.trim()}>
                        {loading ? (
                            <>
                                <div className="spinner" style={{ width: 20, height: 20, borderWidth: 2 }}></div>
                                Tracing...
                            </>
                        ) : (
                            <>
                                <LuMapPin />
                                Trace
                            </>
                        )}
                    </button>
                </div>
                {error && <div className="error-message">{error}</div>}
            </form>

            <div style={{ marginTop: 48, textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 32, flexWrap: 'wrap' }}>
                    {[
                        { icon: '📍', title: 'Location', desc: 'Country & region' },
                        { icon: '📡', title: 'Carrier', desc: 'Network provider' },
                        { icon: '📱', title: 'Line Type', desc: 'Mobile, landline, VoIP' },
                        { icon: '🛡️', title: 'Spam Check', desc: 'Community reports' },
                    ].map(f => (
                        <div key={f.title} style={{
                            textAlign: 'center',
                            padding: '24px 16px',
                            minWidth: 120,
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: 'var(--radius-md)',
                            transition: 'all 0.3s ease',
                        }}>
                            <div style={{ fontSize: '2rem', marginBottom: 8 }}>{f.icon}</div>
                            <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: 4 }}>{f.title}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{f.desc}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default SearchPage;
