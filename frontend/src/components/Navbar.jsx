import { NavLink } from 'react-router-dom';
import { LuTarget, LuSparkles } from 'react-icons/lu';

function Navbar() {
    return (
        <nav className="navbar">
            <NavLink to="/" className="navbar-brand">
                <LuTarget className="brand-icon" />
                PhoneTracer
            </NavLink>
            <div className="navbar-links">
                <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''} end>
                    Search
                </NavLink>
                <NavLink to="/report" className={({ isActive }) => isActive ? 'active' : ''}>
                    Report
                </NavLink>
                <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>
                    History
                </NavLink>
                <NavLink to="/ai" className={({ isActive }) => `nav-ai-link ${isActive ? 'active' : ''}`}>
                    <LuSparkles style={{ fontSize: '0.85rem' }} />
                    AI
                </NavLink>
            </div>
        </nav>
    );
}

export default Navbar;
