# NutriBot Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the NutriBot React frontend into a polished, accessible, mobile-correct "warm wellness" chat UI with a richer welcome screen, without changing behavior or the backend API.

**Architecture:** Semantic CSS-variable design tokens (light + `.dark`) mapped into Tailwind colors replace the JS class-string theme object. The 497-line `ChatInterface.jsx` is split into focused presentational components plus two hooks (`useTheme`, `useSpeech`); `ChatInterface` keeps only state and the translate -> fetch -> translate-back flow.

**Tech Stack:** React 19 (CRA / react-scripts 5), Tailwind 3.4, lucide-react, react-markdown 6 + remark-gfm 1, Jest + @testing-library/react 16 (+ user-event 13).

**Spec:** `docs/superpowers/specs/2026-10-01-ui-redesign-design.md`

## Global Constraints

- Work only inside `react-frontend/` (plus the two doc files already written). **No backend/API changes. No new npm dependencies.**
- All commands run from `C:\Users\risha\OneDrive\Desktop\Projects\Nutri RAG\react-frontend` (the path has spaces - quote it). Shell is bash; run tests with `CI=true npm test -- --watchAll=false`.
- **Do NOT run `git commit`/`git add`.** The user has not asked for commits; leave changes in the working tree. (Ignore any "commit" habit from templates.)
- A dev server is already running in the background on port 3000 (hot reload). **Do not start another one.**
- Python, if ever needed, must be run with the project venv: `C:\Users\risha\OneDrive\Desktop\Projects\Nutri RAG\venv\Scripts\python.exe` (only Task 8 starts the backend).
- Every text/background token pair must be >= 4.5:1 contrast (enforced by `npm run check:contrast`).
- Behavior preservation: translation, backend fetch (`http://localhost:5000/api/search`), citation matching, and text-to-speech logic are moved, not rewritten. The composer placeholder must stay `I am 21, 75kg. Suggest a high protein lunch...` (existing test matches `/suggest a high protein lunch/i`).
- `screen.getByText('NutriBot')` in `App.test.js` must match exactly one element: only the header `<h1>` may have the exact text `NutriBot` on the welcome screen.
- CRA Jest config has `resetMocks: true`: mock implementations must be (re)set inside `beforeEach`/the test, never only at module top level.
- Colors come only from semantic Tailwind tokens (`bg-canvas`, `bg-surface`, `bg-surface-2`, `border-line`, `text-ink`, `text-muted`, `bg-primary`, `text-primary`, `text-primary-fg`, `bg-primary-soft`, `text-accent`, `text-danger`, `bg-danger-soft`). No raw hex in components.
- Touch targets >= 44px (`h-11`/`w-11`); body text 16px (`text-base`).

## File Structure

| File | Responsibility |
|---|---|
| `src/index.css` (rewrite) | Tokens (`:root`, `.dark`), base styles, focus ring, scrollbar, skeleton, reduced-motion |
| `tailwind.config.js` (rewrite) | Map tokens to Tailwind colors; fonts; `darkMode: 'class'` |
| `scripts/check-contrast.js` (new) | Parse tokens from `index.css`, assert WCAG ratios |
| `public/index.html`, `public/manifest.json` | Title, description, theme-color, font links |
| `src/hooks/useTheme.js` (new) | Theme state, persistence, `dark` class on `<html>` |
| `src/hooks/useSpeech.js` (new) | Text-to-speech state (moved from ChatInterface) |
| `src/components/CitationTooltip.jsx` (new) | Portal tooltip for a cited food (moved) |
| `src/components/AssistantAnswer.jsx` (new) | Markdown rendering + citation matching (moved) |
| `src/components/Header.jsx` (new) | Brand, status, New chat, theme toggle |
| `src/components/Composer.jsx` (new) | Input + send |
| `src/components/WelcomeScreen.jsx` (new) | Headline, starter prompts, trust badges |
| `src/components/Message.jsx` (new) | One user / assistant / error message |
| `src/components/MessageList.jsx` (new) | `role="log"` list, thinking skeleton, autoscroll |
| `src/components/ChatInterface.jsx` (rewrite) | State + send flow, composes the above |
| `src/App.js` (rewrite), `src/App.css` (delete) | Wire `useTheme`, drop App.css |

---

### Task 1: Design tokens, Tailwind mapping, fonts, document metadata, contrast check

**Files:**
- Create: `scripts/check-contrast.js`
- Modify: `package.json` (add script), `tailwind.config.js`, `src/index.css`, `public/index.html`, `public/manifest.json`

**Interfaces:**
- Produces: CSS vars `--canvas --surface --surface-2 --line --ink --muted --primary --primary-fg --primary-soft --accent --danger --danger-soft` (space-separated RGB triplets) under `:root` and `.dark`; Tailwind colors `canvas surface surface-2 line ink muted primary primary-fg primary-soft accent danger danger-soft`; fonts `font-sans` (Inter), `font-serif` (Lora), `font-mono` (JetBrains Mono); CSS classes `.skeleton-line`; npm script `check:contrast`.

- [ ] **Step 1: Write the contrast checker (it will fail first: no tokens yet)**

Create `scripts/check-contrast.js`:

```js
// Asserts WCAG AA (4.5:1) for every text/background token pair, in both themes.
// Parses the RGB triplets straight out of src/index.css so it can't drift.
const fs = require('fs');
const path = require('path');

const css = fs.readFileSync(path.join(__dirname, '..', 'src', 'index.css'), 'utf8');

function readBlock(selector) {
  const escaped = selector.replace(/[.]/g, '\\.');
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  if (!match) throw new Error(`token block not found: ${selector}`);
  const vars = {};
  for (const m of match[1].matchAll(/--([a-z0-9-]+):\s*(\d+)\s+(\d+)\s+(\d+)\s*;/g)) {
    vars[m[1]] = [Number(m[2]), Number(m[3]), Number(m[4])];
  }
  return vars;
}

function luminance([r, g, b]) {
  const lin = [r, g, b].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

function ratio(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const PAIRS = [
  ['ink', 'canvas'], ['ink', 'surface'], ['ink', 'surface-2'], ['ink', 'primary-soft'],
  ['muted', 'canvas'], ['muted', 'surface'], ['muted', 'surface-2'],
  ['primary', 'canvas'], ['primary', 'surface'], ['primary', 'primary-soft'],
  ['primary-fg', 'primary'],
  ['accent', 'canvas'], ['accent', 'surface'],
  ['danger', 'danger-soft'],
];

let failed = 0;
for (const [theme, selector] of [['light', ':root'], ['dark', '.dark']]) {
  const vars = readBlock(selector);
  for (const [fg, bg] of PAIRS) {
    if (!vars[fg] || !vars[bg]) throw new Error(`${theme}: missing token ${!vars[fg] ? fg : bg}`);
    const r = ratio(vars[fg], vars[bg]);
    const ok = r >= 4.5;
    if (!ok) failed += 1;
    console.log(`${ok ? 'PASS' : 'FAIL'}  ${theme.padEnd(5)} ${fg} on ${bg}: ${r.toFixed(2)}`);
  }
}
if (failed) {
  console.error(`\n${failed} pair(s) below 4.5:1`);
  process.exit(1);
}
console.log('\nAll token pairs >= 4.5:1');
```

Add to `package.json` `"scripts"`: `"check:contrast": "node scripts/check-contrast.js"`.

- [ ] **Step 2: Run it to verify it fails**

Run: `npm run check:contrast`
Expected: FAIL with `token block not found: :root`.

- [ ] **Step 3: Rewrite `src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Design tokens: space-separated RGB triplets so Tailwind can add alpha. */
:root {
  --canvas: 250 250 247;
  --surface: 255 255 255;
  --surface-2: 243 246 243;
  --line: 218 226 220;
  --ink: 24 33 29;
  --muted: 85 99 92;
  --primary: 4 120 87;
  --primary-fg: 255 255 255;
  --primary-soft: 228 244 236;
  --accent: 194 65 12;
  --danger: 185 28 28;
  --danger-soft: 254 242 242;
  color-scheme: light;
}

.dark {
  --canvas: 14 18 16;
  --surface: 20 26 23;
  --surface-2: 27 35 31;
  --line: 42 54 48;
  --ink: 238 243 240;
  --muted: 148 163 155;
  --primary: 52 211 153;
  --primary-fg: 4 24 17;
  --primary-soft: 17 43 33;
  --accent: 251 146 60;
  --danger: 252 165 165;
  --danger-soft: 69 20 20;
  color-scheme: dark;
}

@layer base {
  html,
  body,
  #root {
    height: 100%;
  }

  body {
    margin: 0;
    background-color: rgb(var(--canvas));
    color: rgb(var(--ink));
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Visible keyboard focus everywhere (never remove the outline). */
  :focus-visible {
    outline: 2px solid rgb(var(--primary));
    outline-offset: 2px;
  }

  ::-webkit-scrollbar {
    width: 8px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: rgb(var(--line));
    border-radius: 4px;
  }
}

/* Shimmer skeleton (thinking indicator) */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton-line {
  height: 0.75rem;
  border-radius: 9999px;
  background-image: linear-gradient(
    90deg,
    rgb(var(--surface-2)) 25%,
    rgb(var(--line)) 50%,
    rgb(var(--surface-2)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.6s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 4: Rewrite `tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

module.exports = {
    darkMode: 'class',
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                canvas: token('canvas'),
                surface: token('surface'),
                'surface-2': token('surface-2'),
                line: token('line'),
                ink: token('ink'),
                muted: token('muted'),
                primary: token('primary'),
                'primary-fg': token('primary-fg'),
                'primary-soft': token('primary-soft'),
                accent: token('accent'),
                danger: token('danger'),
                'danger-soft': token('danger-soft'),
            },
            fontFamily: {
                sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
                serif: ['Lora', 'ui-serif', 'Georgia', 'serif'],
                mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
            },
        },
    },
    plugins: [],
}
```

- [ ] **Step 5: Document metadata and fonts**

Replace `public/index.html` entirely with:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#FAFAF7" media="(prefers-color-scheme: light)" />
    <meta name="theme-color" content="#0E1210" media="(prefers-color-scheme: dark)" />
    <meta
      name="description"
      content="NutriBot is a retrieval-grounded diet assistant: personalized, allergy-aware meal suggestions with cited sources, in your language."
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:wght@500;600;700&family=JetBrains+Mono:wght@500&display=swap"
      rel="stylesheet"
    />
    <title>NutriBot - Personalized Diet Assistant</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
```

In `public/manifest.json` change `"short_name"` to `"NutriBot"`, `"name"` to `"NutriBot - Personalized Diet Assistant"`, `"theme_color"` to `"#047857"`, `"background_color"` to `"#FAFAF7"`.

- [ ] **Step 6: Verify**

Run: `npm run check:contrast`
Expected: every line `PASS`, final `All token pairs >= 4.5:1`. If any pair fails, darken/lighten the failing token in `src/index.css` (not the threshold) until it passes.

Run: `CI=true npm run build`
Expected: `Compiled successfully` (the old components still use their own hex classes, so they are unaffected).

---

### Task 2: `useTheme` hook (TDD)

**Files:**
- Create: `src/hooks/useTheme.js`
- Test: `src/hooks/useTheme.test.js`

**Interfaces:**
- Produces: `export default function useTheme(): { isDark: boolean, toggle: () => void }`. Storage key `'nutribot-theme'` with values `'dark' | 'light'`. Toggles `dark` class and `style.colorScheme` on `document.documentElement`.

- [ ] **Step 1: Write the failing tests**

```js
import { renderHook, act } from '@testing-library/react';
import useTheme from './useTheme';

afterEach(() => {
  document.documentElement.classList.remove('dark');
  localStorage.clear();
  delete window.matchMedia;
  jest.restoreAllMocks();
});

test('defaults to light when nothing is stored and there is no system preference', () => {
  const { result } = renderHook(() => useTheme());
  expect(result.current.isDark).toBe(false);
  expect(document.documentElement.classList.contains('dark')).toBe(false);
});

test('follows the system dark preference when nothing is stored', () => {
  window.matchMedia = jest.fn().mockReturnValue({ matches: true });
  const { result } = renderHook(() => useTheme());
  expect(result.current.isDark).toBe(true);
  expect(document.documentElement.classList.contains('dark')).toBe(true);
});

test('a stored choice wins over the system preference', () => {
  window.matchMedia = jest.fn().mockReturnValue({ matches: true });
  localStorage.setItem('nutribot-theme', 'light');
  const { result } = renderHook(() => useTheme());
  expect(result.current.isDark).toBe(false);
});

test('toggle flips the theme, updates the html class and persists the choice', () => {
  const { result } = renderHook(() => useTheme());
  act(() => result.current.toggle());
  expect(result.current.isDark).toBe(true);
  expect(document.documentElement.classList.contains('dark')).toBe(true);
  expect(localStorage.getItem('nutribot-theme')).toBe('dark');
  act(() => result.current.toggle());
  expect(result.current.isDark).toBe(false);
  expect(localStorage.getItem('nutribot-theme')).toBe('light');
});

test('does not crash when localStorage is blocked', () => {
  jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
  const { result } = renderHook(() => useTheme());
  expect(result.current.isDark).toBe(false);
  act(() => result.current.toggle());
  expect(result.current.isDark).toBe(true);
});
```

- [ ] **Step 2: Run to verify failure**

Run: `CI=true npm test -- --watchAll=false src/hooks/useTheme.test.js`
Expected: FAIL, `Cannot find module './useTheme'`.

- [ ] **Step 3: Implement**

```js
import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'nutribot-theme';

function readStoredTheme() {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === 'dark' || value === 'light' ? value : null;
  } catch (e) {
    return null;
  }
}

function systemPrefersDark() {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export default function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    const stored = readStoredTheme();
    return stored ? stored === 'dark' : systemPrefersDark();
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    document.documentElement.style.colorScheme = isDark ? 'dark' : 'light';
  }, [isDark]);

  const toggle = useCallback(() => {
    const next = !isDark;
    setIsDark(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next ? 'dark' : 'light');
    } catch (e) {
      // Storage can be blocked (private mode); the choice just won't persist.
    }
  }, [isDark]);

  return { isDark, toggle };
}
```

- [ ] **Step 4: Run to verify pass**

Run: `CI=true npm test -- --watchAll=false src/hooks/useTheme.test.js`
Expected: 5 passed.

---

### Task 3: `useSpeech` hook (moved logic, TDD)

**Files:**
- Create: `src/hooks/useSpeech.js`
- Test: `src/hooks/useSpeech.test.js`

**Interfaces:**
- Produces: `export default function useSpeech(): { speakingId: (number|string|null), speak: (text: string, langCode: string|undefined, id: number|string) => void, stop: () => void }`. `stop` has a stable identity. Calling `speak` with the id that is already speaking stops it. Language map: `hi -> hi-IN`, `te -> te-IN`, `en -> en-US`, anything else `en-US`.

- [ ] **Step 1: Write the failing tests**

```js
import { renderHook, act } from '@testing-library/react';
import useSpeech from './useSpeech';

test('speak marks the id as speaking and uses the mapped language', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('namaste', 'hi', 7));
  expect(result.current.speakingId).toBe(7);
  expect(speakSpy).toHaveBeenCalledTimes(1);
  expect(speakSpy.mock.calls[0][0].lang).toBe('hi-IN');
});

test('unknown language codes fall back to en-US', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hola', 'xx', 1));
  expect(speakSpy.mock.calls[0][0].lang).toBe('en-US');
});

test('speaking the same id again stops it', () => {
  const cancelSpy = jest.spyOn(window.speechSynthesis, 'cancel');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hello', 'en', 3));
  act(() => result.current.speak('hello', 'en', 3));
  expect(result.current.speakingId).toBe(null);
  expect(cancelSpy).toHaveBeenCalled();
});

test('speakingId clears when the utterance ends', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hello', 'en', 5));
  act(() => speakSpy.mock.calls[0][0].onend());
  expect(result.current.speakingId).toBe(null);
});

test('stop clears speakingId', () => {
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hello', 'en', 9));
  act(() => result.current.stop());
  expect(result.current.speakingId).toBe(null);
});
```

- [ ] **Step 2: Run to verify failure**

Run: `CI=true npm test -- --watchAll=false src/hooks/useSpeech.test.js`
Expected: FAIL, `Cannot find module './useSpeech'`.

- [ ] **Step 3: Implement**

```js
import { useCallback, useState } from 'react';

const TTS_LANG = { hi: 'hi-IN', te: 'te-IN', en: 'en-US' };

// speakingId is the id of the message currently being read (or null), NOT a
// plain boolean - a shared boolean made every "Read aloud" button show "Stop"
// at once as soon as any one message started speaking.
export default function useSpeech() {
  const [speakingId, setSpeakingId] = useState(null);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setSpeakingId(null);
  }, []);

  const speak = useCallback((text, langCode = 'en', id) => {
    if (speakingId === id) {
      stop();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const targetLang = TTS_LANG[langCode] || 'en-US';
    utterance.lang = targetLang;

    const voices = window.speechSynthesis.getVoices();
    let preferredVoice = voices.find((v) => v.lang.includes(targetLang));
    if (!preferredVoice) {
      preferredVoice = voices.find((v) => v.name.includes('Google') || v.name.includes('Natural'));
    }
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(id);
    window.speechSynthesis.speak(utterance);
  }, [speakingId, stop]);

  return { speakingId, speak, stop };
}
```

- [ ] **Step 4: Run to verify pass**

Run: `CI=true npm test -- --watchAll=false src/hooks/useSpeech.test.js`
Expected: 5 passed.

---

### Task 4: `CitationTooltip` and `AssistantAnswer` (moved, restyled, TDD)

**Files:**
- Create: `src/components/CitationTooltip.jsx`, `src/components/AssistantAnswer.jsx`
- Test: `src/components/AssistantAnswer.test.jsx`

**Interfaces:**
- Produces: `CitationTooltip({ title, text, children })` (default export); `AssistantAnswer({ content: string, sources?: Array<{title: string, text: string}> })` (default export). Neither takes theme props any more.

- [ ] **Step 1: Write the failing tests**

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import AssistantAnswer from './AssistantAnswer';

const sources = [
  { title: 'Oats', text: 'Oats are high in fiber.' },
  { title: 'Ragi (Finger Millet)', text: 'Ragi is rich in calcium.' },
];

test('a bolded retrieved food becomes a citation that reveals its snippet on hover', () => {
  render(<AssistantAnswer content="I chose **Oats** because they have fiber." sources={sources} />);
  const trigger = screen.getByRole('button', { name: 'Oats' });
  expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  fireEvent.mouseEnter(trigger);
  expect(screen.getByRole('tooltip')).toHaveTextContent('Oats are high in fiber.');
  fireEvent.mouseLeave(trigger);
  expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
});

test('a food mentioned by its base name still matches the full retrieved title', () => {
  render(<AssistantAnswer content="Try Ragi porridge for breakfast." sources={sources} />);
  fireEvent.focus(screen.getByRole('button', { name: 'Ragi' }));
  expect(screen.getByRole('tooltip')).toHaveTextContent('Ragi is rich in calcium.');
});

test('text with no retrieved foods renders without citation buttons', () => {
  render(<AssistantAnswer content="Drink more water." sources={sources} />);
  expect(screen.getByText('Drink more water.')).toBeInTheDocument();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});

test('GFM tables render as real tables', () => {
  const md = '| Food | Protein |\n|---|---|\n| Oats | 13g |';
  render(<AssistantAnswer content={md} sources={sources} />);
  expect(screen.getByRole('table')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Oats' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run to verify failure**

Run: `CI=true npm test -- --watchAll=false src/components/AssistantAnswer.test.jsx`
Expected: FAIL, `Cannot find module './AssistantAnswer'`.

- [ ] **Step 3: Create `src/components/CitationTooltip.jsx`**

```jsx
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
```

- [ ] **Step 4: Create `src/components/AssistantAnswer.jsx`**

```jsx
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
        <div className="text-base">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {content}
            </ReactMarkdown>
        </div>
    );
};

export default AssistantAnswer;
```

- [ ] **Step 5: Run to verify pass**

Run: `CI=true npm test -- --watchAll=false src/components/AssistantAnswer.test.jsx`
Expected: 4 passed, and no "does not recognize the `X` prop on a DOM element" warnings in the output.

---

### Task 5: `Header`, `Composer`, `WelcomeScreen` (TDD)

**Files:**
- Create: `src/components/Header.jsx`, `src/components/Composer.jsx`, `src/components/WelcomeScreen.jsx`
- Test: `src/components/Header.test.jsx`, `src/components/Composer.test.jsx`, `src/components/WelcomeScreen.test.jsx`

**Interfaces:**
- Produces:
  - `Header({ isDark: boolean, onToggleTheme: () => void, onNewChat: () => void, isLoading: boolean })`
  - `Composer({ value: string, onChange: (next: string) => void, onSubmit: (e: Event) => void, disabled: boolean })` - note `onChange` receives the string, not the event.
  - `WelcomeScreen({ onPick: (text: string) => void, disabled?: boolean })` and named export `STARTER_PROMPTS` (4 items `{ id, icon, label, text }`).

- [ ] **Step 1: Verify the lucide icons exist (they must, or imports render `undefined`)**

Run: `node -e "const l=require('lucide-react');['Salad','Sun','Moon','Plus','Send','Dumbbell','Egg','HeartPulse','Languages','ShieldCheck','BookMarked','Globe'].forEach(n=>console.log(n, !!l[n]))"`
Expected: every name prints `true`. If one prints `false`, pick a similar existing icon and use that name consistently below.

- [ ] **Step 2: Write the failing tests**

`src/components/Header.test.jsx`:

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import Header from './Header';

const setup = (props = {}) => {
  const handlers = { onToggleTheme: jest.fn(), onNewChat: jest.fn() };
  render(<Header isDark={false} isLoading={false} {...handlers} {...props} />);
  return handlers;
};

test('shows the brand and a New chat button that works', () => {
  const { onNewChat } = setup();
  expect(screen.getByRole('heading', { name: 'NutriBot' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'New chat' }));
  expect(onNewChat).toHaveBeenCalledTimes(1);
});

test('theme button label reflects the current theme and toggles', () => {
  const { onToggleTheme } = setup({ isDark: true });
  fireEvent.click(screen.getByRole('button', { name: 'Switch to light mode' }));
  expect(onToggleTheme).toHaveBeenCalledTimes(1);
});

test('status text switches between Ready and Thinking', () => {
  const { unmount } = render(<Header isDark={false} isLoading={false} onToggleTheme={() => {}} onNewChat={() => {}} />);
  expect(screen.getByRole('status')).toHaveTextContent('Ready');
  unmount();
  render(<Header isDark={false} isLoading onToggleTheme={() => {}} onNewChat={() => {}} />);
  expect(screen.getByRole('status')).toHaveTextContent('Thinking');
});
```

`src/components/Composer.test.jsx`:

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import Composer from './Composer';

test('typing calls onChange with the string value', () => {
  const onChange = jest.fn();
  render(<Composer value="" onChange={onChange} onSubmit={() => {}} disabled={false} />);
  fireEvent.change(screen.getByLabelText(/ask nutribot/i), { target: { value: 'hi' } });
  expect(onChange).toHaveBeenCalledWith('hi');
});

test('send is disabled for empty/whitespace input and while disabled', () => {
  const { rerender } = render(<Composer value="  " onChange={() => {}} onSubmit={() => {}} disabled={false} />);
  expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
  rerender(<Composer value="hello" onChange={() => {}} onSubmit={() => {}} disabled />);
  expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
  rerender(<Composer value="hello" onChange={() => {}} onSubmit={() => {}} disabled={false} />);
  expect(screen.getByRole('button', { name: 'Send message' })).toBeEnabled();
});

test('submitting calls onSubmit', () => {
  const onSubmit = jest.fn((e) => e.preventDefault());
  render(<Composer value="hello" onChange={() => {}} onSubmit={onSubmit} disabled={false} />);
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  expect(onSubmit).toHaveBeenCalledTimes(1);
});
```

`src/components/WelcomeScreen.test.jsx`:

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import WelcomeScreen, { STARTER_PROMPTS } from './WelcomeScreen';

test('renders the headline and one button per starter prompt', () => {
  render(<WelcomeScreen onPick={() => {}} />);
  expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Tell it your goal.');
  expect(STARTER_PROMPTS).toHaveLength(4);
  STARTER_PROMPTS.forEach((p) => {
    expect(screen.getByRole('button', { name: new RegExp(p.label, 'i') })).toBeInTheDocument();
  });
});

test('clicking a starter prompt passes its full text to onPick', () => {
  const onPick = jest.fn();
  render(<WelcomeScreen onPick={onPick} />);
  fireEvent.click(screen.getByRole('button', { name: /egg allergy/i }));
  expect(onPick).toHaveBeenCalledWith(STARTER_PROMPTS.find((p) => p.id === 'allergy').text);
});

test('starter prompts are disabled while a request is in flight', () => {
  render(<WelcomeScreen onPick={() => {}} disabled />);
  screen.getAllByRole('button').forEach((b) => expect(b).toBeDisabled());
});

test('shows the three trust badges and no element with the exact text "NutriBot"', () => {
  render(<WelcomeScreen onPick={() => {}} />);
  expect(screen.getByText('Allergy-aware')).toBeInTheDocument();
  expect(screen.getByText('Cited sources')).toBeInTheDocument();
  expect(screen.getByText('Replies in your language')).toBeInTheDocument();
  expect(screen.queryByText('NutriBot')).not.toBeInTheDocument();
});
```

- [ ] **Step 3: Run to verify failure**

Run: `CI=true npm test -- --watchAll=false src/components/Header.test.jsx src/components/Composer.test.jsx src/components/WelcomeScreen.test.jsx`
Expected: FAIL, modules not found.

- [ ] **Step 4: Implement `Header.jsx`**

```jsx
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
```

- [ ] **Step 5: Implement `Composer.jsx`**

```jsx
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
```

- [ ] **Step 6: Implement `WelcomeScreen.jsx`**

```jsx
import React from 'react';
import { Dumbbell, Egg, HeartPulse, Languages, ShieldCheck, BookMarked, Globe } from 'lucide-react';

export const STARTER_PROMPTS = [
    { id: 'muscle', icon: Dumbbell, label: 'Build muscle', text: "I'm 21 and 75kg. Suggest a high-protein lunch to build muscle." },
    { id: 'allergy', icon: Egg, label: 'Egg allergy', text: "I'm allergic to eggs. Suggest a filling breakfast." },
    { id: 'diabetes', icon: HeartPulse, label: 'Type 2 diabetes', text: "I have type 2 diabetes. What's a good low-sugar dinner?" },
    { id: 'hindi', icon: Languages, label: 'Ask in Hindi', text: 'मुझे वज़न कम करना है, रात के लिए हल्का खाना बताइए।' },
];

const BADGES = [
    { id: 'allergy', icon: ShieldCheck, label: 'Allergy-aware' },
    { id: 'sources', icon: BookMarked, label: 'Cited sources' },
    { id: 'language', icon: Globe, label: 'Replies in your language' },
];

const WelcomeScreen = ({ onPick, disabled = false }) => (
    <section className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-4 py-10 md:px-6">
        <p className="text-sm font-medium text-primary">Grounded in a curated nutrition database</p>
        <h2 className="mt-3 font-serif text-4xl font-semibold leading-tight text-ink md:text-5xl">
            Tell it your goal.
            <br />
            <span className="text-muted">It builds the plan.</span>
        </h2>
        <p className="mt-4 max-w-xl text-lg text-muted">
            Portioned meal ideas with the reason behind each pick. Mention an allergy or condition and it will keep you clear of it.
        </p>

        <ul className="mt-8 grid gap-3 sm:grid-cols-2">
            {STARTER_PROMPTS.map(({ id, icon: Icon, label, text }) => (
                <li key={id}>
                    <button
                        type="button"
                        onClick={() => onPick(text)}
                        disabled={disabled}
                        className="flex min-h-[4.5rem] w-full items-start gap-3 rounded-2xl border border-line bg-surface p-4 text-left transition-colors hover:border-primary disabled:opacity-50"
                    >
                        <span aria-hidden="true" className="mt-0.5 text-accent"><Icon className="h-5 w-5" /></span>
                        <span>
                            <span className="block text-sm font-semibold text-ink">{label}</span>
                            <span className="mt-0.5 block text-sm text-muted">{text}</span>
                        </span>
                    </button>
                </li>
            ))}
        </ul>

        <ul className="mt-8 flex flex-wrap gap-x-5 gap-y-2">
            {BADGES.map(({ id, icon: Icon, label }) => (
                <li key={id} className="flex items-center gap-2 text-sm text-muted">
                    <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
                    <span>{label}</span>
                </li>
            ))}
        </ul>
    </section>
);

export default WelcomeScreen;
```

- [ ] **Step 7: Run to verify pass**

Run: `CI=true npm test -- --watchAll=false src/components/Header.test.jsx src/components/Composer.test.jsx src/components/WelcomeScreen.test.jsx`
Expected: all passed.

---

### Task 6: `Message` and `MessageList` (TDD)

**Files:**
- Create: `src/components/Message.jsx`, `src/components/MessageList.jsx`
- Test: `src/components/Message.test.jsx`, `src/components/MessageList.test.jsx`

**Interfaces:**
- Consumes: `AssistantAnswer({ content, sources })` from Task 4.
- Produces:
  - Message shape: `{ id: number|string, role: 'user'|'assistant', content: string, sources?: Array<{title,text}>, langCode?: string, isError?: boolean, timestamp: Date }`
  - `Message({ message, isSpeaking: boolean, onSpeak: (text, langCode, id) => void })`
  - `MessageList({ messages, isLoading: boolean, speakingId: (number|string|null), onSpeak })`

- [ ] **Step 1: Write the failing tests**

`src/components/Message.test.jsx`:

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import Message from './Message';

const base = { id: 1, timestamp: new Date() };

test('user messages render their text', () => {
  render(<Message message={{ ...base, role: 'user', content: 'hello there' }} isSpeaking={false} onSpeak={() => {}} />);
  expect(screen.getByText('hello there')).toBeInTheDocument();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});

test('errors render as an alert with no read-aloud control', () => {
  render(<Message message={{ ...base, role: 'assistant', isError: true, content: 'Could not reach the server.' }} isSpeaking={false} onSpeak={() => {}} />);
  expect(screen.getByRole('alert')).toHaveTextContent('Could not reach the server.');
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});

test('assistant messages offer read aloud and pass id and language to onSpeak', () => {
  const onSpeak = jest.fn();
  render(<Message message={{ ...base, id: 42, role: 'assistant', content: 'Eat oats.', sources: [], langCode: 'hi' }} isSpeaking={false} onSpeak={onSpeak} />);
  fireEvent.click(screen.getByRole('button', { name: /read aloud/i }));
  expect(onSpeak).toHaveBeenCalledWith('Eat oats.', 'hi', 42);
});

test('the button reads Stop while this message is being spoken', () => {
  render(<Message message={{ ...base, role: 'assistant', content: 'Eat oats.', sources: [] }} isSpeaking onSpeak={() => {}} />);
  expect(screen.getByRole('button', { name: /stop/i })).toHaveAttribute('aria-pressed', 'true');
});
```

`src/components/MessageList.test.jsx`:

```jsx
import { render, screen } from '@testing-library/react';
import MessageList from './MessageList';

const msgs = [
  { id: 1, role: 'user', content: 'plan my lunch', timestamp: new Date() },
  { id: 2, role: 'assistant', content: 'Try lentils.', sources: [], timestamp: new Date() },
];

test('renders an accessible live log with every message', () => {
  render(<MessageList messages={msgs} isLoading={false} speakingId={null} onSpeak={() => {}} />);
  const log = screen.getByRole('log', { name: 'Conversation' });
  expect(log).toHaveAttribute('aria-live', 'polite');
  expect(screen.getByText('plan my lunch')).toBeInTheDocument();
  expect(screen.getByText('Try lentils.')).toBeInTheDocument();
});

test('shows a thinking placeholder only while loading', () => {
  const { rerender } = render(<MessageList messages={msgs} isLoading={false} speakingId={null} onSpeak={() => {}} />);
  expect(screen.queryByText('NutriBot is thinking')).not.toBeInTheDocument();
  rerender(<MessageList messages={msgs} isLoading speakingId={null} onSpeak={() => {}} />);
  expect(screen.getByText('NutriBot is thinking')).toBeInTheDocument();
});

test('only the speaking message shows Stop', () => {
  const two = [...msgs, { id: 3, role: 'assistant', content: 'Or rice.', sources: [], timestamp: new Date() }];
  render(<MessageList messages={two} isLoading={false} speakingId={2} onSpeak={() => {}} />);
  expect(screen.getAllByRole('button', { name: /stop/i })).toHaveLength(1);
  expect(screen.getAllByRole('button', { name: /read aloud/i })).toHaveLength(1);
});
```

- [ ] **Step 2: Run to verify failure**

Run: `CI=true npm test -- --watchAll=false src/components/Message.test.jsx src/components/MessageList.test.jsx`
Expected: FAIL, modules not found.

- [ ] **Step 3: Implement `Message.jsx`**

```jsx
import React from 'react';
import { Volume2, StopCircle, AlertTriangle, Salad } from 'lucide-react';
import AssistantAnswer from './AssistantAnswer';

const Message = ({ message, isSpeaking, onSpeak }) => {
    if (message.role === 'user') {
        return (
            <div className="flex justify-end">
                <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary-soft px-4 py-3 text-base leading-relaxed text-ink md:max-w-[75%]">
                    {message.content}
                </div>
            </div>
        );
    }

    if (message.isError) {
        return (
            <div role="alert" className="flex items-start gap-3 rounded-2xl bg-danger-soft px-4 py-3 text-base leading-relaxed text-danger">
                <AlertTriangle className="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{message.content}</span>
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
```

- [ ] **Step 4: Implement `MessageList.jsx`**

```jsx
import React, { useEffect, useRef } from 'react';
import Message from './Message';

const MessageList = ({ messages, isLoading, speakingId, onSpeak }) => {
    const endRef = useRef(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
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
```

- [ ] **Step 5: Run to verify pass**

Run: `CI=true npm test -- --watchAll=false src/components/Message.test.jsx src/components/MessageList.test.jsx`
Expected: all passed.

---

### Task 7: Rewrite `ChatInterface` and `App`, delete `App.css`, integration tests

**Files:**
- Modify (full rewrite): `src/components/ChatInterface.jsx`, `src/App.js`
- Delete: `src/App.css`
- Test: `src/components/ChatInterface.test.jsx` (new), `src/App.test.js` (extend)

**Interfaces:**
- Consumes: everything from Tasks 2-6.
- Produces: `ChatInterface({ isDark, onToggleTheme, onNewChat, resetCounter })` (default export); `App` default export.

- [ ] **Step 1: Write the failing integration tests**

`src/components/ChatInterface.test.jsx`:

```jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatInterface from './ChatInterface';
import { translate } from '../utils/translator';

jest.mock('../utils/translator', () => ({ translate: jest.fn() }));

const renderChat = (props = {}) =>
  render(<ChatInterface isDark={false} onToggleTheme={() => {}} onNewChat={() => {}} resetCounter={0} {...props} />);

beforeEach(() => {
  translate.mockImplementation(async (text) => ({ text, from: { language: { iso: 'en' } } }));
  global.fetch = jest.fn().mockResolvedValue({
    json: async () => ({
      success: true,
      answer: 'Try **Oats** with milk.',
      sources: [{ title: 'Oats', text: 'Oats are high in fiber.' }],
    }),
  });
});

test('shows the welcome screen until the first message', () => {
  renderChat();
  expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Tell it your goal.');
  expect(screen.queryByRole('log')).not.toBeInTheDocument();
});

test('clicking a starter prompt sends it and renders the cited answer', async () => {
  renderChat();
  fireEvent.click(screen.getByRole('button', { name: /build muscle/i }));
  expect(await screen.findByRole('button', { name: 'Oats' })).toBeInTheDocument();
  expect(screen.getByText(/high-protein lunch to build muscle/i)).toBeInTheDocument();
  const [url, init] = global.fetch.mock.calls[0];
  expect(url).toBe('http://localhost:5000/api/search');
  expect(JSON.parse(init.body).query).toMatch(/high-protein lunch to build muscle/i);
  expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument();
});

test('typing a question and submitting sends it', async () => {
  renderChat();
  fireEvent.change(screen.getByLabelText(/ask nutribot/i), { target: { value: 'low carb dinner' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  await screen.findByRole('button', { name: 'Oats' });
  expect(JSON.parse(global.fetch.mock.calls[0][1].body).query).toBe('low carb dinner');
  expect(screen.getByLabelText(/ask nutribot/i)).toHaveValue('');
});

test('a network failure shows an error alert instead of crashing', async () => {
  global.fetch = jest.fn().mockRejectedValue(new Error('down'));
  renderChat();
  fireEvent.change(screen.getByLabelText(/ask nutribot/i), { target: { value: 'hello' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/could not reach the server/i);
});

test('non-English input is translated for the backend and the answer is translated back', async () => {
  translate.mockImplementation(async (text, { to }) =>
    to === 'en'
      ? { text: 'light dinner', from: { language: { iso: 'hi' } } }
      : { text: 'हल्का रात का खाना', from: { language: { iso: 'en' } } }
  );
  renderChat();
  fireEvent.change(screen.getByLabelText(/ask nutribot/i), { target: { value: 'हल्का खाना' } });
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  expect(await screen.findByText('हल्का रात का खाना')).toBeInTheDocument();
  expect(JSON.parse(global.fetch.mock.calls[0][1].body).query).toBe('light dinner');
});

test('bumping resetCounter clears the conversation and restores the welcome screen', async () => {
  const { rerender } = renderChat({ resetCounter: 0 });
  fireEvent.click(screen.getByRole('button', { name: /build muscle/i }));
  await screen.findByRole('button', { name: 'Oats' });
  rerender(<ChatInterface isDark={false} onToggleTheme={() => {}} onNewChat={() => {}} resetCounter={1} />);
  await waitFor(() => expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument());
  expect(screen.queryByRole('log')).not.toBeInTheDocument();
});
```

Replace `src/App.test.js` with:

```js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({ json: async () => ({ success: true }) });
});

afterEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove('dark');
});

test('renders the NutriBot chat shell', () => {
  render(<App />);
  expect(screen.getByText('NutriBot')).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/suggest a high protein lunch/i)).toBeInTheDocument();
});

test('the theme toggle switches the html class and remembers the choice', () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: 'Switch to dark mode' }));
  expect(document.documentElement.classList.contains('dark')).toBe(true);
  expect(localStorage.getItem('nutribot-theme')).toBe('dark');
  expect(screen.getByRole('button', { name: 'Switch to light mode' })).toBeInTheDocument();
});

test('New chat tells the backend to clear its history', async () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: 'New chat' }));
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  const [url, init] = global.fetch.mock.calls[0];
  expect(url).toBe('http://localhost:5000/api/search');
  expect(JSON.parse(init.body).query).toBe('RESET_CHAT');
});
```

- [ ] **Step 2: Run to verify failure**

Run: `CI=true npm test -- --watchAll=false src/components/ChatInterface.test.jsx src/App.test.js`
Expected: FAIL (old ChatInterface has no starter prompts / labelled buttons).

- [ ] **Step 3: Rewrite `src/components/ChatInterface.jsx`**

```jsx
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
```

- [ ] **Step 4: Rewrite `src/App.js` and delete `src/App.css`**

```jsx
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
    <div className="h-dvh bg-canvas text-ink">
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
```

Run: `rm src/App.css`

- [ ] **Step 5: Run the whole suite**

Run: `CI=true npm test -- --watchAll=false`
Expected: all test files pass (hooks, components, App). Fix any failure in the implementation, not by weakening a test.

---

### Task 8: Full verification, real end-to-end check, final rating

**Files:** none created unless a defect is found (then fix in the owning file and re-run the affected tests).

- [ ] **Step 1: Static checks**

Run: `CI=true npm test -- --watchAll=false`  -> all pass
Run: `npm run check:contrast` -> all PASS
Run: `CI=true npm run build` -> `Compiled successfully` with no warnings
Run: `grep -rnE "isDarkMode|#[0-9A-Fa-f]{6}|bg-\[#|text-\[#|border-\[#" src --include=*.js --include=*.jsx --include=*.css | grep -v "\.test\."`
Expected: no matches except the `:root`/`.dark` token comments (the tokens are RGB triplets, so there should be none). Any hit in a component is a leftover raw color: replace it with a token.

- [ ] **Step 2: Start the backend with the project venv**

Run in background (bash), from the repo root:
`cd "C:/Users/risha/OneDrive/Desktop/Projects/Nutri RAG/backend" && "../venv/Scripts/python.exe" server.py`
Wait until `curl -s http://127.0.0.1:5000/health` returns `{"status":"ok"}` (model load can take a minute or two). If startup fails (missing `OLLAMA_API_KEY`, no network), report the exact error and skip Steps 3's real-answer part; do not edit `backend/.env`.

- [ ] **Step 3: Visual and responsive verification in the Browser pane**

Use the Browser tools on `http://localhost:3000`:
1. Light and dark: set via the header toggle; confirm `document.documentElement.classList.contains('dark')` flips and the page re-themes.
2. For each viewport (375x812 mobile preset, 768x1024 tablet preset, desktop), run in `javascript_tool`: `({sw: document.documentElement.scrollWidth, iw: window.innerWidth})`. Expected `sw <= iw` (no horizontal scroll). Also check the New chat button is visible at 375 (`document.querySelector('[aria-label="New chat"]').getBoundingClientRect().width > 0`).
3. Click the "Build muscle" starter; expect a real answer with citation buttons; hover/focus one and confirm the tooltip shows the snippet. Take screenshots if the pane renders (if screenshots time out, rely on `read_page`/`get_page_text` and the DOM checks above and say so).
4. Keyboard: Tab through the page; confirm a visible focus outline (`getComputedStyle(document.activeElement).outlineStyle !== 'none'`).
5. Reset the viewport to the `desktop` preset when done.

- [ ] **Step 4: Stop the backend**, leave the dev server running.

- [ ] **Step 5: Report**

Produce: test/build/contrast results, the viewport/overflow results, any defects found and fixed, and an honest after-rating out of 10 with the specific remaining weaknesses.
