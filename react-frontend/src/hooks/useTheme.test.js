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
