// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// jsdom doesn't implement scrollIntoView (it's a real-layout browser API) -
// ChatInterface calls it on every message update, so any test that renders
// it needs this stubbed out or the effect throws.
if (typeof window !== 'undefined') {
  window.HTMLElement.prototype.scrollIntoView = window.HTMLElement.prototype.scrollIntoView || function () {};
}

// jsdom doesn't implement the Web Speech API at all - ChatInterface calls
// window.speechSynthesis.cancel() on mount/reset and builds a
// SpeechSynthesisUtterance for the read-aloud button, so both need a stub
// or any test rendering it throws.
if (typeof window !== 'undefined' && !window.speechSynthesis) {
  window.speechSynthesis = {
    cancel: () => {},
    speak: () => {},
    getVoices: () => [],
  };
}
if (typeof window !== 'undefined' && !window.SpeechSynthesisUtterance) {
  window.SpeechSynthesisUtterance = function (text) {
    this.text = text;
  };
}
