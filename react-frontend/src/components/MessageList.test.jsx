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
