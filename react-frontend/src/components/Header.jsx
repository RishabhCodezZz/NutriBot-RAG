import React from 'react';
import { Salad, Sun, Moon, Plus } from 'lucide-react';

const Header = ({ isDark, onToggleTheme, onNewChat, isLoading }) => (
    <header className="border-b border-line bg-surface">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-3 md:px-6">
            <div className="flex min-w-0 items-center gap-3">
                <div aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
                    <Salad className="h-6 w-6" />
                </div>
                <div className="min-w-0">
                    <h1 className="font-serif text-xl font-semibold leading-tight text-ink">NutriBot</h1>
                    <p className="truncate text-sm text-muted">Your personalized diet assistant</p>
                </div>
            </div>

            <div className="flex shrink-0 items-center gap-2">
                <span role="status" className="flex items-center gap-2 px-1 text-sm text-muted">
                    <span aria-hidden="true" className={`h-2 w-2 rounded-full ${isLoading ? 'animate-pulse bg-accent' : 'bg-primary'}`} />
                    <span className="sr-only sm:not-sr-only">{isLoading ? 'Thinking' : 'Ready'}</span>
                </span>

                <button
                    type="button"
                    onClick={onNewChat}
                    aria-label="New chat"
                    className="flex h-11 items-center gap-1.5 rounded-full border border-line px-3.5 text-sm text-muted transition-colors hover:border-primary hover:text-primary"
                >
                    <Plus className="h-4 w-4" aria-hidden="true" />
                    <span className="hidden sm:inline">New chat</span>
                </button>

                <button
                    type="button"
                    onClick={onToggleTheme}
                    aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                    className="flex h-11 w-11 items-center justify-center rounded-full border border-line text-muted transition-colors hover:border-primary hover:text-primary"
                >
                    {isDark ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
                </button>
            </div>
        </div>
    </header>
);

export default Header;
