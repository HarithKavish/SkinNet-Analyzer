import React from 'react';
import './App.css';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import '@fortawesome/fontawesome-free/css/all.min.css';
import Navbar from './components/Navbar';
import HomePage from './components/Home';
import Apage from './components/Ab';
import Upload from './components/Upload';
// import Formm from './Components/Formm';
// import AIChatbotResult from './Components/AIBotResult';

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<Apage />} />
        <Route path="/upload" element={<Upload />} />
      </Routes>
    </Router>
  );
}

export default App;
