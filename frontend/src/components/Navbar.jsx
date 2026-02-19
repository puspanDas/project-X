import { NavLink } from 'react-router-dom';
import { MdTrackChanges, MdAutoAwesome } from 'react-icons/md';

function Navbar() {
    return (
        <nav className="navbar">
            <NavLink to="/" className="navbar-brand">
                <MdTrackChanges className="brand-icon" />
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
                    <MdAutoAwesome style={{ fontSize: '0.85rem' }} />
                    AI
                </NavLink>
            </div>
        </nav>
    );
}

export default Navbar;
