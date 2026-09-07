import React, { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [resetCounter, setResetCounter] = useState(0);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleNewChat = async () => {
    // Clears backend chat history and triggers a frontend reset
    try {
      await fetch('http://localhost:5000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'RESET_CHAT' }),
      });
    } catch (e) {
      // Non-blocking; UI still resets
      console.warn('Failed to reset backend history', e);
    } finally {
      setResetCounter((prev) => prev + 1);
    }
  };

  return (
    <div className={`flex h-screen ${isDarkMode ? 'dark bg-[#0A0A0B]' : 'bg-[#FAFAF9]'}`}>
      <div className="flex-1 flex flex-col">
        <ChatInterface
          isDarkMode={isDarkMode}
          onToggleDarkMode={toggleDarkMode}
          onNewChat={handleNewChat}
          resetCounter={resetCounter}
        />
      </div>
    </div>
  );
}

export default App;
