import React from 'react';
import { Send } from 'lucide-react';

const Composer = ({ value, onChange, onSubmit, disabled }) => (
    <div className="border-t border-line bg-surface">
        <form onSubmit={onSubmit} className="mx-auto flex w-full max-w-3xl items-center gap-3 px-4 py-3 md:px-6 md:py-4">
            <label htmlFor="chat-input" className="sr-only">Ask NutriBot about food and nutrition</label>
            <input
                id="chat-input"
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="I am 21, 75kg. Suggest a high protein lunch..."
                autoComplete="off"
                className="h-12 min-w-0 flex-1 rounded-full border border-line bg-canvas px-5 text-base text-ink placeholder:text-muted focus:border-primary"
            />
            <button
                type="submit"
                disabled={disabled || !value.trim()}
                aria-label="Send message"
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary text-primary-fg transition-opacity hover:opacity-90 disabled:opacity-40"
            >
                <Send className="h-5 w-5" aria-hidden="true" />
            </button>
        </form>
    </div>
);

export default Composer;
