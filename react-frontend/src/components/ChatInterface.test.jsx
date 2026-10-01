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
  const errSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  try {
    global.fetch = jest.fn().mockRejectedValue(new Error('down'));
    renderChat();
    fireEvent.change(screen.getByLabelText(/ask nutribot/i), { target: { value: 'hello' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not reach the server/i);
    expect(errSpy).toHaveBeenCalledWith('Chat Error:', expect.any(Error));
  } finally {
    errSpy.mockRestore();
  }
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
