import { render, screen, fireEvent } from '@testing-library/react';
import WelcomeScreen, { STARTER_PROMPTS } from './WelcomeScreen';

test('renders the headline and one button per starter prompt', () => {
  render(<WelcomeScreen onPick={() => {}} />);
  expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Tell it your goal.');
  expect(STARTER_PROMPTS).toHaveLength(4);
  STARTER_PROMPTS.forEach((p) => {
    expect(screen.getByRole('button', { name: new RegExp(p.label, 'i') })).toBeInTheDocument();
  });
});

test('clicking a starter prompt passes its full text to onPick', () => {
  const onPick = jest.fn();
  render(<WelcomeScreen onPick={onPick} />);
  fireEvent.click(screen.getByRole('button', { name: /egg allergy/i }));
  expect(onPick).toHaveBeenCalledWith(STARTER_PROMPTS.find((p) => p.id === 'allergy').text);
});

test('starter prompts are disabled while a request is in flight', () => {
  render(<WelcomeScreen onPick={() => {}} disabled />);
  screen.getAllByRole('button').forEach((b) => expect(b).toBeDisabled());
});

test('shows the three trust badges and no element with the exact text "NutriBot"', () => {
  render(<WelcomeScreen onPick={() => {}} />);
  expect(screen.getByText('Allergy-aware')).toBeInTheDocument();
  expect(screen.getByText('Cited sources')).toBeInTheDocument();
  expect(screen.getByText('Replies in your language')).toBeInTheDocument();
  expect(screen.queryByText('NutriBot')).not.toBeInTheDocument();
});
