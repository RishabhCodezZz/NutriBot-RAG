import React, { useState, useRef, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { Send, Sun, Moon, Volume2, Salad, StopCircle, Plus, AlertTriangle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { translate } from '../utils/translator';

// Escapes a string for safe use inside a RegExp alternation.
const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const TOOLTIP_WIDTH = 224; // px, matches the w-56 below

// Renders its tooltip via a portal straight into <body>, positioned from the
// trigger's real viewport coordinates - this is what lets it escape the
// markdown table wrapper's `overflow-x-auto`, which (per the CSS overflow
// spec) silently forces overflow-y to `auto` too and would otherwise clip
// any citation that lands inside a table cell.
const CitationTooltip = ({ title, text, t, isDarkMode, children }) => {
    const triggerRef = useRef(null);
    const [pos, setPos] = useState(null);

    const show = () => {
        const rect = triggerRef.current?.getBoundingClientRect();
        if (!rect) return;
        const left = Math.min(Math.max(8, rect.left), window.innerWidth - TOOLTIP_WIDTH - 8);
        setPos({ top: rect.top, left });
    };
    const hide = () => setPos(null);

    return (
        <>
            <button
                ref={triggerRef}
                type="button"
                onMouseEnter={show}
                onMouseLeave={hide}
                onFocus={show}
                onBlur={hide}
                className="underline decoration-dotted decoration-emerald-500/70 underline-offset-2 hover:decoration-solid hover:text-emerald-500 transition-colors"
            >
                {children}
            </button>
            {pos && createPortal(
                <div
                    style={{ position: 'fixed', top: pos.top, left: pos.left, transform: 'translateY(-100%) translateY(-6px)' }}
                    className={`pointer-events-none z-50 w-56 max-w-[75vw] rounded-xl border p-3 text-left text-xs shadow-lg ${t.panelBorder} ${isDarkMode ? 'bg-[#16161A] text-[#F2F2F3]' : 'bg-white text-[#18181B]'}`}
                >
                    <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-emerald-500">{title}</div>
                    <div className={`leading-relaxed ${t.textDim}`}>{text}</div>
                </div>,
                document.body
            )}
        </>
    );
};

// Turns bolded/table/list food names in an answer into hover citations that
// reveal the real retrieved snippet behind them - matched deterministically
// against what was actually retrieved, not a citation the model asserts about
// itself (LLMs get self-citations wrong; this can't, it's just string matching).
const AssistantAnswer = ({ content, sources, t, isDarkMode }) => {
    const { regex, sourceByTitleLower } = useMemo(() => {
        const map = {};
        const patterns = new Set();
        (sources || []).forEach((s) => {
            if (!s.title) return;
            const title = s.title.trim();
            if (!map[title.toLowerCase()]) map[title.toLowerCase()] = s;
            patterns.add(title);
            // Also match the food's base name without a trailing parenthetical
            // qualifier - e.g. "Ragi (Finger Millet)" -> "Ragi" - since the
            // model paraphrases the same food with different descriptors
            // ("Ragi (as a side grain)", "Ragi (small serving)") that don't
            // contain the full canonical title verbatim, which is why some
            // mentions of the same food were getting cited and others weren't.
            const base = title.replace(/\s*\([^)]*\)\s*$/, '').trim();
            if (base.length >= 3 && base.toLowerCase() !== title.toLowerCase() && !map[base.toLowerCase()]) {
                map[base.toLowerCase()] = s;
                patterns.add(base);
            }
        });
        if (!patterns.size) return { regex: null, sourceByTitleLower: {} };
        // Longest pattern first, so e.g. "Chicken Thigh (cooked)" wins over
        // the shorter "Chicken Thigh" base alias when the full phrase is
        // actually present, rather than the base alias grabbing part of it.
        const pattern = [...patterns].sort((a, b) => b.length - a.length).map(escapeRegExp).join('|');
        // Lookaround instead of \b: several titles end in a closing paren
        // (e.g. "Chicken Thigh (cooked)"), and \b right after ")" would
        // never match since ")" to a following space/period is a
        // non-word-to-non-word transition, not a boundary.
        return { regex: new RegExp(`(?<![A-Za-z0-9])(${pattern})(?![A-Za-z0-9])`, 'gi'), sourceByTitleLower: map };
    }, [sources]);

    // Only processes direct string children - nested elements (e.g. a
    // <strong> inside a <li>) are matched independently when react-markdown
    // renders that nested component, so this stays shallow on purpose.
    const cite = (children, keyPrefix) => {
        if (!regex) return children;
        const arr = Array.isArray(children) ? children : [children];
        return arr.map((child, i) => {
            if (typeof child !== 'string') return child;
            const parts = child.split(regex);
            if (parts.length === 1) return child;
            return parts.map((part, j) => {
                const source = sourceByTitleLower[part.toLowerCase()];
                if (!source) {
                    return <React.Fragment key={`${keyPrefix}-${i}-${j}`}>{part}</React.Fragment>;
                }
                return (
                    <CitationTooltip key={`${keyPrefix}-${i}-${j}`} title={source.title} text={source.text} t={t} isDarkMode={isDarkMode}>
                        {part}
                    </CitationTooltip>
                );
            });
        });
    };

    const markdownComponents = {
        p: ({ node, children, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed" {...props}>{cite(children, 'p')}</p>,
        strong: ({ node, children, ...props }) => <strong className="font-bold" {...props}>{cite(children, 'strong')}</strong>,
        // react-markdown v6's renderer API (pinned for Jest/CRA compatibility -
        // see package.json) passes extra semantic props alongside the usual
        // DOM ones - level/depth/ordered/checked/index/isHeader - that don't
        // exist on v9+. Each override below explicitly destructures and drops
        // them before spreading the rest onto the real DOM element, or React
        // logs "does not recognize the `X` prop on a DOM element" for each one.
        h1: ({ node, level, ...props }) => <h3 className="text-base font-bold mt-4 mb-2 first:mt-0" {...props} />,
        h2: ({ node, level, ...props }) => <h3 className="text-base font-bold mt-4 mb-2 first:mt-0" {...props} />,
        h3: ({ node, level, ...props }) => <h4 className={`text-sm font-bold mt-3 mb-1.5 first:mt-0 ${t.textDim}`} {...props} />,
        // list-outside (not list-inside): gpt-oss often puts block content
        // (its own paragraph) inside a single list item, and list-inside's
        // marker ends up stranded on its own line above that block instead
        // of next to it - list-outside with left padding keeps the number
        // beside the first line of content regardless.
        ul: ({ node, depth, ordered, ...props }) => <ul className="list-disc list-outside pl-5 space-y-1 mb-3" {...props} />,
        ol: ({ node, depth, ordered, ...props }) => <ol className="list-decimal list-outside pl-5 space-y-1 mb-3" {...props} />,
        li: ({ node, children, checked, index, ordered, ...props }) => <li className="leading-relaxed" {...props}>{cite(children, 'li')}</li>,
        hr: () => <hr className={`my-4 ${t.panelBorder}`} />,
        code: ({ node, inline, ...props }) =>
            inline
                ? <code className={`font-mono text-[0.85em] px-1.5 py-0.5 rounded-md ${isDarkMode ? 'bg-white/10' : 'bg-black/5'}`} {...props} />
                : <code className="font-mono text-[0.85em] block" {...props} />,
        table: ({ node, ...props }) => (
            <div className={`my-3 overflow-x-auto rounded-2xl border ${t.panelBorder}`}>
                <table className="w-full text-xs md:text-sm border-collapse" {...props} />
            </div>
        ),
        thead: ({ node, ...props }) => <thead className={isDarkMode ? 'bg-white/5' : 'bg-black/5'} {...props} />,
        th: ({ node, isHeader, ...props }) => (
            <th className={`text-left font-mono uppercase tracking-wider text-[10px] px-3 py-2 border-b ${t.panelBorder} ${t.textDim}`} {...props} />
        ),
        td: ({ node, children, isHeader, ...props }) => <td className={`px-3 py-2 border-b ${t.panelBorder} align-top`} {...props}>{cite(children, 'td')}</td>,
        a: ({ node, ...props }) => <a className="underline text-emerald-500 hover:text-emerald-400" target="_blank" rel="noreferrer" {...props} />,
    };

    return (
        <div className="text-sm md:text-base">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {content}
            </ReactMarkdown>
        </div>
    );
};

const ChatInterface = ({ isDarkMode, onToggleDarkMode, onNewChat, resetCounter }) => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    // Which message's audio is currently playing (or null) - NOT a plain
    // boolean, since a boolean is shared by every message's button and made
    // every "Read Aloud" button in the whole chat show "Stop" at once as
    // soon as any one of them started speaking.
    const [speakingId, setSpeakingId] = useState(null);

    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // === IMPROVED TEXT TO SPEECH (WITH MULTI-LANGUAGE SUPPORT) ===
    const speakText = (text, langCode = 'en', id) => {
        if (speakingId === id) {
            window.speechSynthesis.cancel();
            setSpeakingId(null);
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);

        const ttsLangMap = {
            'hi': 'hi-IN',
            'te': 'te-IN',
            'en': 'en-US'
        };

        const targetLang = ttsLangMap[langCode] || 'en-US';
        utterance.lang = targetLang;

        const voices = window.speechSynthesis.getVoices();
        let preferredVoice = voices.find(v => v.lang.includes(targetLang));

        if (!preferredVoice) {
            preferredVoice = voices.find(v => v.name.includes('Google') || v.name.includes('Natural'));
        }

        if (preferredVoice) utterance.voice = preferredVoice;

        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        utterance.onend = () => setSpeakingId(null);
        utterance.onerror = () => setSpeakingId(null);

        setSpeakingId(id);
        window.speechSynthesis.speak(utterance);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        // 1. Translate input to English - a separate try/catch from the backend
        // call below, so a translate hiccup (the free gtx endpoint rate-limits
        // or errors sometimes) degrades to sending the raw text instead of
        // being misreported as "Could not reach the server" - it never
        // touched the backend at all.
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
            const response = await fetch('http://localhost:5000/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: englishText })
            });

            const data = await response.json();

            if (data.success) {
                let finalAnswer = data.answer;

                // Translate the bot's response back to the user's language.
                // Note: citations match against the original English source
                // titles, so they only link up when the answer is still in
                // English - a translated answer still reads fine, it just
                // won't have clickable citations. Same graceful-degradation
                // approach as the input translation above: show the English
                // answer rather than erroring the whole reply out.
                if (targetOutputLang !== 'en') {
                    try {
                        const translatedOutputRes = await translate(finalAnswer, { to: targetOutputLang });
                        finalAnswer = translatedOutputRes.text;
                    } catch (error) {
                        console.warn('Output translation failed, showing the English answer:', error);
                    }
                }

                const aiMessage = {
                    id: Date.now() + 1,
                    role: 'assistant',
                    content: finalAnswer,
                    sources: data.sources || [],
                    timestamp: new Date(),
                    langCode: targetOutputLang // Save language for Voice Reader
                };
                setMessages(prev => [...prev, aiMessage]);
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
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                isError: true,
                content: "Could not reach the server. Make sure your Python backend is running on port 5000.",
                timestamp: new Date()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const hasMessages = messages.length > 0;

    useEffect(() => {
        setMessages([]);
        setInputValue('');
        window.speechSynthesis.cancel();
        setSpeakingId(null);
    }, [resetCounter]);

    // Theme tokens - kept in one place so dark/light stay in lockstep with the
    // same accent + monospace treatment instead of two hand-maintained sets
    // of Tailwind class strings sprinkled through the JSX.
    const t = isDarkMode
        ? {
            bg: 'bg-[#0A0A0B]',
            headerBg: 'bg-[#0A0A0B]',
            border: 'border-[#1F1F22]',
            panel: 'bg-[#111113]',
            panelBorder: 'border-[#1F1F22]',
            text: 'text-[#F2F2F3]',
            textDim: 'text-[#7A7A81]',
            userBubble: 'bg-[#12201A] text-[#F2F2F3] border border-[#1E3A2C]',
            botBubble: 'bg-[#111113] text-[#F2F2F3] border border-[#1F1F22]',
            errorBubble: 'bg-red-950/40 text-red-300 border border-red-500/40',
            inputBg: 'bg-[#111113] border-[#1F1F22] text-[#F2F2F3] placeholder-[#5A5A61]',
            skeleton: 'skeleton-line-dark',
        }
        : {
            bg: 'bg-[#FAFAF9]',
            headerBg: 'bg-white',
            border: 'border-[#E7E5E4]',
            panel: 'bg-white',
            panelBorder: 'border-[#E7E5E4]',
            text: 'text-[#18181B]',
            textDim: 'text-[#8A8A91]',
            userBubble: 'bg-[#F0FBF5] text-[#18181B] border border-[#CFEEDC]',
            botBubble: 'bg-white text-[#18181B] border border-[#E7E5E4]',
            errorBubble: 'bg-red-50 text-red-700 border border-red-200',
            inputBg: 'bg-white border-[#E7E5E4] text-[#18181B] placeholder-[#A8A8AD]',
            skeleton: 'skeleton-line-light',
        };

    return (
        <div className={`flex flex-col h-screen w-full ${t.bg}`}>

            {/* Top Navigation */}
            <div className={`flex items-center justify-between px-6 py-4 border-b ${t.border} ${t.headerBg}`}>
                <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-2xl ${isDarkMode ? 'bg-emerald-950/60 text-emerald-500' : 'bg-emerald-50 text-emerald-600'}`}>
                        <Salad className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className={`text-lg font-bold leading-tight ${t.text}`}>
                            NutriBot
                        </h1>
                        <p className={`text-[11px] font-mono uppercase tracking-widest ${t.textDim}`}>
                            Your personalized diet assistant
                        </p>
                    </div>
                </div>

                <div className="flex items-center space-x-3">
                    {/* Status pill */}
                    <span className={`hidden sm:flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest px-3 py-1.5 rounded-full border ${t.panelBorder} ${t.textDim}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${isLoading ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`} />
                        {isLoading ? 'Thinking' : 'Ready'}
                    </span>

                    <button
                        onClick={onNewChat}
                        className={`hidden sm:flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-widest px-3 py-1.5 rounded-full border transition-colors ${t.panelBorder} ${t.textDim} hover:text-emerald-500 hover:border-emerald-500/40`}
                    >
                        <Plus className="w-3.5 h-3.5" />
                        New Chat
                    </button>

                    <button onClick={onToggleDarkMode} className={`p-2 rounded-full transition-colors border ${t.panelBorder} ${isDarkMode ? 'hover:bg-[#1C1C1F] text-[#B8B8BD]' : 'hover:bg-gray-100 text-gray-600'}`}>
                        {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                    </button>
                </div>
            </div>

            {/* Chat History */}
            <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-8 flex flex-col space-y-6">
                {!hasMessages && (
                    <div className="flex-1 flex flex-col items-center justify-center text-center space-y-5 px-4">
                        <span className="text-[11px] font-mono uppercase tracking-[0.3em] text-emerald-500">
                            RAG &middot; Diet Assistant
                        </span>
                        <h2 className="leading-[1.05]">
                            <span className={`block text-4xl md:text-5xl font-extrabold ${t.text}`}>Tell it your goal.</span>
                            <span className={`block text-4xl md:text-5xl font-extrabold ${t.textDim}`}>It builds the plan.</span>
                        </h2>
                    </div>
                )}

                {messages.map((message) => {
                    const isUser = message.role === 'user';
                    const isError = !!message.isError;
                    const isSpeakingThis = speakingId === message.id;
                    return (
                        <div key={message.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                            <span className={`mb-1.5 text-[10px] font-mono uppercase tracking-widest ${isUser ? t.textDim : 'text-emerald-500'}`}>
                                {isUser ? 'You' : isError ? 'Error' : 'NutriBot'}
                            </span>
                            <div className={`max-w-[90%] md:max-w-[75%] rounded-3xl px-6 py-4 shadow-sm ${isUser ? t.userBubble : isError ? t.errorBubble : t.botBubble
                                }`}>

                                {isError ? (
                                    <div className="flex items-start gap-2.5 text-sm md:text-base leading-relaxed">
                                        <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                        <span>{message.content}</span>
                                    </div>
                                ) : isUser ? (
                                    <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                                        {message.content}
                                    </div>
                                ) : (
                                    <AssistantAnswer content={message.content} sources={message.sources} t={t} isDarkMode={isDarkMode} />
                                )}

                                {/* READ ALOUD BUTTON */}
                                {message.role === 'assistant' && !isError && (
                                    <div className={`mt-4 pt-3 border-t flex items-center justify-between ${t.panelBorder}`}>
                                        <button
                                            onClick={() => speakText(message.content, message.langCode, message.id)}
                                            className={`flex items-center space-x-2 text-[11px] font-mono uppercase tracking-wider transition-colors px-3 py-1.5 rounded-full border ${isSpeakingThis
                                                    ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-500'
                                                    : `${t.panelBorder} ${t.textDim} hover:text-emerald-500 hover:border-emerald-500/40`
                                                }`}
                                        >
                                            {isSpeakingThis ? <StopCircle className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                                            <span>{isSpeakingThis ? 'Stop' : 'Read Aloud'}</span>
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}

                {isLoading && (
                    <div className="flex flex-col items-start">
                        <span className="mb-1.5 text-[10px] font-mono uppercase tracking-widest text-emerald-500">NutriBot</span>
                        <div className={`w-full max-w-[70%] rounded-3xl px-6 py-4 space-y-2.5 shadow-sm ${t.botBubble}`}>
                            <div className={`skeleton-line ${t.skeleton} w-[85%]`} />
                            <div className={`skeleton-line ${t.skeleton} w-[95%]`} />
                            <div className={`skeleton-line ${t.skeleton} w-[60%]`} />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className={`p-4 md:p-6 border-t ${t.border} ${t.headerBg}`}>
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center space-x-4">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="I am 21, 75kg. Suggest a high protein lunch..."
                        className={`flex-1 px-6 py-4 rounded-full border focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/60 transition-all ${t.inputBg}`}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || isLoading}
                        className="p-4 rounded-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white shadow-md transition-colors"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
