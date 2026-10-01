import React, { useEffect, useState } from 'react';
import { translate } from '../utils/translator';
import useSpeech from '../hooks/useSpeech';
import Header from './Header';
import WelcomeScreen from './WelcomeScreen';
import MessageList from './MessageList';
import Composer from './Composer';

const API_URL = 'http://localhost:5000/api/search';

const ChatInterface = ({ isDark, onToggleTheme, onNewChat, resetCounter }) => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { speakingId, speak, stop } = useSpeech();

    const send = async (rawText) => {
        if (!rawText.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: rawText,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        // 1. Translate input to English - a separate try/catch from the backend
        // call below, so a translate hiccup (the free gtx endpoint rate-limits
        // or errors sometimes) degrades to sending the raw text instead of
        // being misreported as "Could not reach the server".
        let englishText = userMessage.content;
        let targetOutputLang = 'en'; // always reply in whatever language the user typed in - auto-detected, never a manual override
        try {
            const englishInputRes = await translate(userMessage.content, { to: 'en' });
            englishText = englishInputRes.text;
            targetOutputLang = englishInputRes.from?.language?.iso || 'en';
        } catch (error) {
            console.warn('Input translation failed, sending the original text as-is:', error);
        }

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: englishText })
            });

            const data = await response.json();

            if (data.success) {
                let finalAnswer = data.answer;

                // Translate the bot's response back to the user's language.
                // Citations match against the original English source titles,
                // so they only link up when the answer is still in English - a
                // translated answer still reads fine, it just won't have
                // clickable citations.
                if (targetOutputLang !== 'en') {
                    try {
                        const translatedOutputRes = await translate(finalAnswer, { to: targetOutputLang });
                        finalAnswer = translatedOutputRes.text;
                    } catch (error) {
                        console.warn('Output translation failed, showing the English answer:', error);
                    }
                }

                setMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: finalAnswer,
                    sources: data.sources || [],
                    timestamp: new Date(),
                    langCode: targetOutputLang // saved for the read-aloud voice
                }]);
            } else {
                setMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    role: 'assistant',
                    isError: true,
                    content: "I'm having trouble connecting to the database. Please try again.",
                    timestamp: new Date()
                }]);
            }
        } catch (error) {
            console.error('Chat Error:', error);
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                isError: true,
                content: 'Could not reach the server. Make sure your Python backend is running on port 5000.',
                timestamp: new Date()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        send(inputValue);
    };

    useEffect(() => {
        setMessages([]);
        setInputValue('');
        stop();
    }, [resetCounter, stop]);

    return (
        <div className="flex h-full w-full flex-col bg-canvas">
            <Header isDark={isDark} onToggleTheme={onToggleTheme} onNewChat={onNewChat} isLoading={isLoading} />

            <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">
                {messages.length === 0 ? (
                    <WelcomeScreen onPick={send} disabled={isLoading} />
                ) : (
                    <MessageList messages={messages} isLoading={isLoading} speakingId={speakingId} onSpeak={speak} />
                )}
            </main>

            <Composer value={inputValue} onChange={setInputValue} onSubmit={handleSubmit} disabled={isLoading} />
        </div>
    );
};

export default ChatInterface;
