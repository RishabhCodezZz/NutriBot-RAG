import React, { useRef, useState } from 'react';
import { createPortal } from 'react-dom';

const TOOLTIP_WIDTH = 224; // px, matches the w-56 below

// Renders its tooltip via a portal straight into <body>, positioned from the
// trigger's real viewport coordinates - this is what lets it escape the
// markdown table wrapper's `overflow-x-auto`, which (per the CSS overflow
// spec) silently forces overflow-y to `auto` too and would otherwise clip
// any citation that lands inside a table cell.
const CitationTooltip = ({ title, text, children }) => {
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
                className="underline decoration-dotted decoration-primary/70 underline-offset-2 transition-colors hover:text-primary hover:decoration-solid"
            >
                {children}
            </button>
            {pos && createPortal(
                <div
                    role="tooltip"
                    style={{ position: 'fixed', top: pos.top, left: pos.left, transform: 'translateY(-100%) translateY(-6px)' }}
                    className="pointer-events-none z-50 w-56 max-w-[75vw] rounded-xl border border-line bg-surface p-3 text-left text-xs text-ink shadow-lg"
                >
                    <div className="mb-1 font-mono text-[11px] uppercase tracking-wider text-primary">{title}</div>
                    <div className="leading-relaxed text-muted">{text}</div>
                </div>,
                document.body
            )}
        </>
    );
};

export default CitationTooltip;
