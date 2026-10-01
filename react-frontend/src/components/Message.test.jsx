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
