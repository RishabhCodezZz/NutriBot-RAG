import { renderHook, act } from '@testing-library/react';
import useSpeech from './useSpeech';

test('speak marks the id as speaking and uses the mapped language', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('namaste', 'hi', 7));
  expect(result.current.speakingId).toBe(7);
  expect(speakSpy).toHaveBeenCalledTimes(1);
  expect(speakSpy.mock.calls[0][0].lang).toBe('hi-IN');
});

test('unknown language codes fall back to en-US', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hola', 'xx', 1));
  expect(speakSpy.mock.calls[0][0].lang).toBe('en-US');
});

test('speaking the same id again stops it', () => {
  const cancelSpy = jest.spyOn(window.speechSynthesis, 'cancel');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hello', 'en', 3));
  act(() => result.current.speak('hello', 'en', 3));
  expect(result.current.speakingId).toBe(null);
  expect(cancelSpy).toHaveBeenCalled();
});

test('speakingId clears when the utterance ends', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hello', 'en', 5));
  act(() => speakSpy.mock.calls[0][0].onend());
  expect(result.current.speakingId).toBe(null);
});

test('a stale utterance error does not clear the newer one', () => {
  const speakSpy = jest.spyOn(window.speechSynthesis, 'speak');
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('first', 'en', 1));
  act(() => result.current.speak('second', 'en', 2));
  expect(result.current.speakingId).toBe(2);
  act(() => speakSpy.mock.calls[0][0].onerror());
  expect(result.current.speakingId).toBe(2);
  act(() => speakSpy.mock.calls[1][0].onend());
  expect(result.current.speakingId).toBe(null);
});

test('stop clears speakingId', () => {
  const { result } = renderHook(() => useSpeech());
  act(() => result.current.speak('hello', 'en', 9));
  act(() => result.current.stop());
  expect(result.current.speakingId).toBe(null);
});
