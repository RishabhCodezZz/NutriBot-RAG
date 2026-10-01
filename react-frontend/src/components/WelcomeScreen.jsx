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
