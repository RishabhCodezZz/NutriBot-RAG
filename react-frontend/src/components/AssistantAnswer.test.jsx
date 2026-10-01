import { render, screen, fireEvent } from '@testing-library/react';
import AssistantAnswer from './AssistantAnswer';

const sources = [
  { title: 'Oats', text: 'Oats are high in fiber.' },
  { title: 'Ragi (Finger Millet)', text: 'Ragi is rich in calcium.' },
];

test('a bolded retrieved food becomes a citation that reveals its snippet on hover', () => {
  render(<AssistantAnswer content="I chose **Oats** because they have fiber." sources={sources} />);
  const trigger = screen.getByRole('button', { name: 'Oats' });
  expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  fireEvent.mouseEnter(trigger);
  expect(screen.getByRole('tooltip')).toHaveTextContent('Oats are high in fiber.');
  fireEvent.mouseLeave(trigger);
  expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
});

test('a food mentioned by its base name still matches the full retrieved title', () => {
  render(<AssistantAnswer content="Try Ragi porridge for breakfast." sources={sources} />);
  fireEvent.focus(screen.getByRole('button', { name: 'Ragi' }));
  expect(screen.getByRole('tooltip')).toHaveTextContent('Ragi is rich in calcium.');
});

test('text with no retrieved foods renders without citation buttons', () => {
  render(<AssistantAnswer content="Drink more water." sources={sources} />);
  expect(screen.getByText('Drink more water.')).toBeInTheDocument();
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});

test('GFM tables render as real tables', () => {
  const md = '| Food | Protein |\n|---|---|\n| Oats | 13g |';
  render(<AssistantAnswer content={md} sources={sources} />);
  expect(screen.getByRole('table')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Oats' })).toBeInTheDocument();
});
