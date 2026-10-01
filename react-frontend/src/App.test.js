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
