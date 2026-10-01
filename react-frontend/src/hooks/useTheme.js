import { useCallback, useLayoutEffect, useState } from 'react';

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

  useLayoutEffect(() => {
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
