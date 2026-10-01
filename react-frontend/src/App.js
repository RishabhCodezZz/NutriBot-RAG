import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import useTheme from './hooks/useTheme';

function App() {
  const { isDark, toggle } = useTheme();
  const [resetCounter, setResetCounter] = useState(0);

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
    <div className="h-screen h-dvh bg-canvas text-ink">
      <ChatInterface
        isDark={isDark}
        onToggleTheme={toggle}
        onNewChat={handleNewChat}
        resetCounter={resetCounter}
      />
    </div>
  );
}

export default App;
