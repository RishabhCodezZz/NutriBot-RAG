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
