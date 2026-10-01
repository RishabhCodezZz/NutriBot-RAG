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

test('New chat is disabled while a request is in flight', () => {
  const { onNewChat } = setup({ isLoading: true });
  const button = screen.getByRole('button', { name: 'New chat' });
  expect(button).toBeDisabled();
  fireEvent.click(button);
  expect(onNewChat).not.toHaveBeenCalled();
});

test('New chat is enabled when idle', () => {
  setup({ isLoading: false });
  expect(screen.getByRole('button', { name: 'New chat' })).toBeEnabled();
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
