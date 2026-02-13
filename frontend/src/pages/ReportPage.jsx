import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { MdReportProblem } from 'react-icons/md';
import { reportNumber } from '../api';

const REPORT_TYPES = [
    'Spam',
    'Scam',
    'Fraud',
    'Telemarketer',
    'Robocall',
    'Phishing',
    'Harassment',
    'Other',
];

function ReportPage() {
    const location = useLocation();
    const prefillNumber = location.state?.number || '';

    const [number, setNumber] = useState(prefillNumber);
    const [type, setType] = useState('Spam');
    const [description, setDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState(null);

    const showToast = (msg, variant = 'success') => {
        setToast({ msg, variant });
        setTimeout(() => setToast(null), 3000);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!number.trim()) return;

        setLoading(true);
        try {
            await reportNumber({
                number: number.trim(),
                type: type.toLowerCase(),
                description: description.trim(),
            });
            showToast('✅ Report submitted successfully!', 'success');
            if (!prefillNumber) setNumber('');
            setDescription('');
        } catch (err) {
            showToast('❌ ' + (err.response?.data?.detail || 'Failed to submit report.'), 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h1 className="page-title">
                <MdReportProblem className="icon" style={{ color: 'var(--accent-warning)' }} />
                Report a Number
            </h1>

            <div className="glass-card">
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Phone Number (with country code)</label>
                        <input
                            className="form-input"
                            type="tel"
                            placeholder="+14158586273"
                            value={number}
                            onChange={e => setNumber(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Report Type</label>
                        <select
                            className="form-select"
                            value={type}
                            onChange={e => setType(e.target.value)}
                        >
                            {REPORT_TYPES.map(t => (
                                <option key={t} value={t}>{t}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Description (optional)</label>
                        <textarea
                            className="form-textarea"
                            placeholder="What happened? e.g. 'Called at 2am claiming to be from bank'"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                        />
                    </div>

                    <button className="form-submit" type="submit" disabled={loading || !number.trim()}>
                        {loading ? 'Submitting...' : '🛡️ Submit Report'}
                    </button>
                </form>
            </div>

            {toast && (
                <div className={`toast ${toast.variant}`}>
                    {toast.msg}
                </div>
            )}
        </div>
    );
}

export default ReportPage;
