import { useState, useRef, useEffect } from 'react';
import { LuSparkles, LuSend, LuBot, LuUser } from 'react-icons/lu';
import { aiChat } from '../api';

const SUGGESTION_CHIPS = [
    "How to identify scam calls?",
    "How to block unwanted numbers?",
    "What is VoIP?",
    "How to report spam?",
    "Caller ID spoofing explained",
    "Phone privacy tips",
    "What are robocalls?",
    "Is it safe to answer unknown numbers?",
];

function AIInsightsPage() {
    const [messages, setMessages] = useState([
        {
            role: 'ai',
            text: "👋 **Hello! I'm your Phone Safety AI Assistant.**\n\nI can help you with:\n\n• 🔍 How to identify scam and spam calls\n• 🛡️ How to block unwanted numbers\n• 📋 How and where to report fraud\n• 📡 Understanding VoIP and virtual numbers\n• 🎭 Caller ID spoofing explained\n• 🔒 Phone privacy and data protection tips\n\nJust ask me anything about phone safety! 💬",
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async (text) => {
        if (!text.trim() || loading) return;

        const userMsg = { role: 'user', text: text.trim() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await aiChat(text.trim(), messages);
            setMessages(prev => [...prev, { role: 'ai', text: res.response }]);
        } catch (err) {
            console.error("AI Chat Error:", err);
            setMessages(prev => [...prev, { role: 'ai', text: "❌ Sorry, something went wrong. Please try again." }]);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        sendMessage(input);
    };

    const handleChip = (text) => {
        setInput(text);
        sendMessage(text);
    };

    // Simple markdown-like formatting
    const formatText = (text) => {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br />');
    };

    return (
        <div>
            {/* Hero */}
            <div className="ai-hero">
                <div className="ai-hero-icon">
                    <LuSparkles />
                </div>
                <h1 className="ai-hero-title">AI Safety Assistant</h1>
                <p className="ai-hero-subtitle">
                    Your intelligent companion for phone safety. Ask anything about scams,
                    spam calls, privacy protection, and more.
                </p>
            </div>

            {/* Chat Container */}
            <div className="glass-card ai-chat-container">
                {/* Messages */}
                <div className="ai-messages">
                    {messages.map((msg, i) => (
                        <div key={i} className={`ai-message ${msg.role}`} style={{ animationDelay: `${i * 0.05}s` }}>
                            <div className="ai-message-avatar">
                                {msg.role === 'ai' ? <LuBot /> : <LuUser />}
                            </div>
                            <div
                                className="ai-message-bubble"
                                dangerouslySetInnerHTML={{ __html: formatText(msg.text) }}
                            />
                        </div>
                    ))}
                    {loading && (
                        <div className="ai-message ai">
                            <div className="ai-message-avatar"><LuBot /></div>
                            <div className="ai-message-bubble">
                                <div className="ai-typing">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={chatEndRef} />
                </div>

                {/* Suggestion Chips */}
                {messages.length <= 1 && (
                    <div className="ai-chips">
                        {SUGGESTION_CHIPS.map(chip => (
                            <button
                                key={chip}
                                className="ai-chip"
                                onClick={() => handleChip(chip)}
                                disabled={loading}
                            >
                                {chip}
                            </button>
                        ))}
                    </div>
                )}

                {/* Input */}
                <form className="ai-input-bar" onSubmit={handleSubmit}>
                    <input
                        type="text"
                        className="ai-input"
                        placeholder="Ask about phone safety..."
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button className="ai-send-btn" type="submit" disabled={loading || !input.trim()}>
                        <LuSend />
                    </button>
                </form>
            </div>
        </div>
    );
}

export default AIInsightsPage;
