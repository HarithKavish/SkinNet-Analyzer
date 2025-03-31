import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/logo.png';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <ul>
        <li>
            <img src={logo} alt='logo'></img>
            <h1>SkinNet Analyzer</h1>
        </li>
        <li><Link to="/">Home</Link></li>
        <li><Link to="/about">About</Link></li>
        <li><Link to="/upload">Upload</Link></li>
        {/* <li><Link to="/form">Symptoms</Link></li> */}
        {/* <li><Link to="/chatbot">AI Chatbot</Link></li> */}
      </ul>
    </nav>
  );
}

export default Navbar;
