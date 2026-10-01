# NutriBot Frontend Redesign - Design

Date: 2026-10-01. Scope: `react-frontend/` only. No backend/API changes, no new npm packages.

## Goal
Raise the UI from a 6/10 to a polished, accessible, mobile-correct health-product interface: "warm wellness hybrid" direction (Lora headlines, Inter body, emerald primary, orange macro accent, flat surfaces), richer empty state, fixed accessibility and mobile bugs.

## Non-goals
Profile panel, chat-history sidebar, backend changes, new dependencies, behavior changes to translation / fetch / citation matching / TTS.

## 1. Design tokens
- CSS variables in `src/index.css` for `:root` (light) and `.dark`: `--bg --surface --surface-2 --border --text --muted --primary --primary-fg --primary-soft --accent --danger --danger-soft`.
- `tailwind.config.js` maps them to semantic colors (`bg-bg`, `bg-surface`, `text-muted`, `bg-primary`, `text-accent`, ...) using `rgb(var(--x) / <alpha-value>)` so opacity utilities work. Fonts: `serif` = Lora, `sans` = Inter, `mono` = JetBrains Mono (citation tooltip title only).
- Every text/background token pair must be >= 4.5:1 (checked by a script in the plan).
- Theme: `useTheme` hook. Default = `prefers-color-scheme`; persisted in `localStorage` inside try/catch; applies `dark` class to `<html>`. `App.js` stops hardcoding dark.
- Remove the JS class-string theme object `t` from ChatInterface.

## 2. Component structure (`src/components/`)
`Header`, `WelcomeScreen`, `MessageList`, `Message`, `AssistantAnswer` (contains `CitationTooltip`, moved verbatim in behavior), `Composer`; hooks in `src/hooks/`: `useTheme`, `useSpeech` (the existing speakText logic). `ChatInterface` keeps state + the submit flow (translate -> fetch -> translate back) unchanged and composes the pieces.
- One centred column `max-w-3xl` for header content, messages, composer.
- Assistant message: no bubble, small avatar, flat text. User message: right-aligned tinted bubble (`primary-soft`). Errors: danger-soft block with icon.

## 3. Welcome screen
Lora headline + one-line promise; four starter prompts (muscle-building lunch, allergy case, diabetes case, Hindi query) as buttons that submit immediately; three trust badges: allergy-aware, cited sources, replies in your language.

## 4. Fixes
- New Chat visible on mobile (icon-only below `sm`); status shown as a dot + sr-only text.
- `:focus-visible` ring on all interactive elements; remove `*:focus { outline:none }`.
- `aria-label` on icon-only buttons; message list `role="log"` + `aria-live="polite"`.
- Remove global `* { transition }` and button hover `translateY`; add `prefers-reduced-motion` guard; keep shimmer skeleton (disabled to a static block under reduced motion).
- `public/index.html`: real title, description, theme-color (per theme not required; single value ok).
- Delete `App.css` (and its import); single stylesheet `index.css`.
- No horizontal overflow at 375px; header never clips.

## 5. Verification
- Jest: keep `App.test.js` passing; add tests: starter prompt click submits, New Chat clears messages, theme choice persists, theme storage failure does not crash.
- `npm run build` passes with no new warnings.
- Manual/automated viewport check at 375 / 768 / 1440 in both themes.
- Contrast script over token pairs.
- One real end-to-end answer through the backend started with `venv\Scripts\python.exe` to confirm tables/citations render in the new style.

## Deviations
- `backend/config.py` default CORS origins now also include `http://127.0.0.1:3000` (opening the app via 127.0.0.1 was blocked and showed "Could not reach the server").
- Token names became `--canvas` / `--line` / `--ink` etc. instead of `--bg` / `--border` / `--text` (the plan adopted them to avoid classes like `bg-bg`).
