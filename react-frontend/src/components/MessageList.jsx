import React, { useEffect, useRef } from 'react';
import Message from './Message';

const MessageList = ({ messages, isLoading, speakingId, onSpeak }) => {
    const endRef = useRef(null);

    useEffect(() => {
        const reduceMotion = typeof window.matchMedia === 'function'
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        endRef.current?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth' });
    }, [messages, isLoading]);

    return (
        <div
            role="log"
            aria-live="polite"
            aria-label="Conversation"
            className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-6 md:px-6"
        >
            {messages.map((message) => (
                <Message
                    key={message.id}
                    message={message}
                    isSpeaking={speakingId === message.id}
                    onSpeak={onSpeak}
                />
            ))}

            {isLoading && (
                <div className="flex items-start gap-3">
                    <span className="sr-only">NutriBot is thinking</span>
                    <div aria-hidden="true" className="mt-0.5 h-8 w-8 shrink-0 rounded-full bg-primary-soft" />
                    <div aria-hidden="true" className="w-full max-w-[70%] space-y-2.5 pt-2">
                        <div className="skeleton-line w-[85%]" />
                        <div className="skeleton-line w-[95%]" />
                        <div className="skeleton-line w-[60%]" />
                    </div>
                </div>
            )}
            <div ref={endRef} />
        </div>
    );
};

export default MessageList;
