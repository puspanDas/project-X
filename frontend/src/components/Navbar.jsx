import { NavLink } from 'react-router-dom';
import { MdTrackChanges } from 'react-icons/md';

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
            </div>
        </nav>
    );
}

export default Navbar;
