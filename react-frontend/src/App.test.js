import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the NutriBot chat shell', () => {
  render(<App />);
  expect(screen.getByText('NutriBot')).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/suggest a high protein lunch/i)).toBeInTheDocument();
});
