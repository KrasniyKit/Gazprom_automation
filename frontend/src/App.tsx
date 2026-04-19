import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from '@/components/layout/Sidebar';
import PassportUpload from '@/pages/PassportUpload';
import PassportCards from '@/pages/PassportCards';

const App: React.FC = () => {
  return (
    <Router>
      <div style={{ display: 'flex', width: '100%', height: '100%' }}>
        <Sidebar />
        <Routes>
          <Route path="/" element={<PassportUpload />} />
          <Route path="/passports" element={<PassportCards />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;

