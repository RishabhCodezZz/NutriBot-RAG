import React from 'react';
import { Volume2, StopCircle, AlertTriangle, Salad } from 'lucide-react';
import AssistantAnswer from './AssistantAnswer';

const Message = ({ message, isSpeaking, onSpeak }) => {
    if (message.role === 'user') {
        return (
            <div className="flex justify-end">
                <div className="max-w-[85%] break-words whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary-soft px-4 py-3 text-base leading-relaxed text-ink md:max-w-[75%]">
                    {message.content}
                </div>
            </div>
        );
    }

    if (message.isError) {
        return (
            <div role="alert" className="flex items-start gap-3 rounded-2xl bg-danger-soft px-4 py-3 text-base leading-relaxed text-danger">
                <AlertTriangle className="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
                <span className="break-words">{message.content}</span>
            </div>
        );
    }

    return (
        <div className="flex items-start gap-3">
            <div aria-hidden="true" className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Salad className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1 text-ink">
                <AssistantAnswer content={message.content} sources={message.sources} />
                <button
                    type="button"
                    onClick={() => onSpeak(message.content, message.langCode, message.id)}
                    aria-pressed={isSpeaking}
                    className={`mt-3 flex h-11 items-center gap-2 rounded-full border px-4 text-sm transition-colors ${
                        isSpeaking
                            ? 'border-primary bg-primary-soft text-primary'
                            : 'border-line text-muted hover:border-primary hover:text-primary'
                    }`}
                >
                    {isSpeaking ? <StopCircle className="h-4 w-4" aria-hidden="true" /> : <Volume2 className="h-4 w-4" aria-hidden="true" />}
                    <span>{isSpeaking ? 'Stop' : 'Read aloud'}</span>
                </button>
            </div>
        </div>
    );
};

export default Message;
