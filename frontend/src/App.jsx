import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Landing from './components/Landing';
import ProgressTracker from './components/ProgressTracker';
import ResultPage from './components/ResultPage';

export default function App() {
  return (
    <>
      <Header />
      <main style={{ paddingTop: '80px' }}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/progress/:jobIds" element={<ProgressTracker />} />
          <Route path="/v/:id" element={<ResultPage />} />
        </Routes>
      </main>
    </>
  );
}
