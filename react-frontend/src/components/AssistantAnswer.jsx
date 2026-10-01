import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CitationTooltip from './CitationTooltip';

// Escapes a string for safe use inside a RegExp alternation.
const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// Turns bolded/table/list food names in an answer into hover citations that
// reveal the real retrieved snippet behind them - matched deterministically
// against what was actually retrieved, not a citation the model asserts about
// itself (LLMs get self-citations wrong; this can't, it's just string matching).
const AssistantAnswer = ({ content, sources }) => {
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
            // model paraphrases the same food with different descriptors.
            const base = title.replace(/\s*\([^)]*\)\s*$/, '').trim();
            if (base.length >= 3 && base.toLowerCase() !== title.toLowerCase() && !map[base.toLowerCase()]) {
                map[base.toLowerCase()] = s;
                patterns.add(base);
            }
        });
        if (!patterns.size) return { regex: null, sourceByTitleLower: {} };
        // Longest pattern first, so the full "Chicken Thigh (cooked)" wins over
        // the shorter base alias. Plain \b is a correct left boundary (titles
        // start with a letter); the right side uses a lookahead because some
        // titles end in ")" where \b would never match.
        const pattern = [...patterns].sort((a, b) => b.length - a.length).map(escapeRegExp).join('|');
        return { regex: new RegExp(`\\b(${pattern})(?![A-Za-z0-9])`, 'gi'), sourceByTitleLower: map };
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
                    <CitationTooltip key={`${keyPrefix}-${i}-${j}`} title={source.title} text={source.text}>
                        {part}
                    </CitationTooltip>
                );
            });
        });
    };

    // react-markdown v6 (pinned for Jest/CRA compatibility) passes extra
    // semantic props (level/depth/ordered/checked/index/isHeader) that don't
    // exist on v9+. Each override destructures and drops them before spreading
    // the rest onto the DOM element, or React warns about unknown DOM props.
    const markdownComponents = {
        p: ({ node, children, ...props }) => <p className="mb-3 leading-relaxed last:mb-0" {...props}>{cite(children, 'p')}</p>,
        strong: ({ node, children, ...props }) => <strong className="font-semibold" {...props}>{cite(children, 'strong')}</strong>,
        h1: ({ node, level, children, ...props }) => <h3 className="mb-2 mt-5 font-serif text-lg font-semibold first:mt-0" {...props}>{children}</h3>,
        h2: ({ node, level, children, ...props }) => <h3 className="mb-2 mt-5 font-serif text-lg font-semibold first:mt-0" {...props}>{children}</h3>,
        h3: ({ node, level, children, ...props }) => <h4 className="mb-1.5 mt-4 text-base font-semibold text-muted first:mt-0" {...props}>{children}</h4>,
        // list-outside (not list-inside): the model often puts a block
        // paragraph inside one list item, and list-inside strands the marker
        // on its own line above that block.
        ul: ({ node, depth, ordered, ...props }) => <ul className="mb-3 list-outside list-disc space-y-1 pl-5" {...props} />,
        ol: ({ node, depth, ordered, ...props }) => <ol className="mb-3 list-outside list-decimal space-y-1 pl-5" {...props} />,
        li: ({ node, children, checked, index, ordered, ...props }) => <li className="leading-relaxed" {...props}>{cite(children, 'li')}</li>,
        hr: () => <hr className="my-4 border-line" />,
        code: ({ node, inline, ...props }) =>
            inline
                ? <code className="rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-[0.85em]" {...props} />
                : <code className="block font-mono text-[0.85em]" {...props} />,
        table: ({ node, ...props }) => (
            <div className="my-3 overflow-x-auto rounded-xl border border-line">
                <table className="w-full border-collapse text-sm" {...props} />
            </div>
        ),
        thead: ({ node, ...props }) => <thead className="bg-surface-2" {...props} />,
        th: ({ node, isHeader, ...props }) => (
            <th className="border-b border-line px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted" {...props} />
        ),
        td: ({ node, children, isHeader, ...props }) => <td className="border-b border-line px-3 py-2 align-top" {...props}>{cite(children, 'td')}</td>,
        a: ({ node, children, ...props }) => <a className="text-primary underline hover:no-underline" target="_blank" rel="noreferrer" {...props}>{children}</a>,
    };

    return (
        <div className="text-base break-words">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {content}
            </ReactMarkdown>
        </div>
    );
};

export default AssistantAnswer;
