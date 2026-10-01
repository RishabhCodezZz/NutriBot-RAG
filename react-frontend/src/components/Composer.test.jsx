import { render, screen, fireEvent } from '@testing-library/react';
import Composer from './Composer';

test('typing calls onChange with the string value', () => {
  const onChange = jest.fn();
  render(<Composer value="" onChange={onChange} onSubmit={() => {}} disabled={false} />);
  fireEvent.change(screen.getByLabelText(/ask nutribot/i), { target: { value: 'hi' } });
  expect(onChange).toHaveBeenCalledWith('hi');
});

test('send is disabled for empty/whitespace input and while disabled', () => {
  const { rerender } = render(<Composer value="  " onChange={() => {}} onSubmit={() => {}} disabled={false} />);
  expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
  rerender(<Composer value="hello" onChange={() => {}} onSubmit={() => {}} disabled />);
  expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
  rerender(<Composer value="hello" onChange={() => {}} onSubmit={() => {}} disabled={false} />);
  expect(screen.getByRole('button', { name: 'Send message' })).toBeEnabled();
});

test('submitting calls onSubmit', () => {
  const onSubmit = jest.fn((e) => e.preventDefault());
  render(<Composer value="hello" onChange={() => {}} onSubmit={onSubmit} disabled={false} />);
  fireEvent.click(screen.getByRole('button', { name: 'Send message' }));
  expect(onSubmit).toHaveBeenCalledTimes(1);
});
