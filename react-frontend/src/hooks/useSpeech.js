import { useCallback, useState } from 'react';

const TTS_LANG = { hi: 'hi-IN', te: 'te-IN', en: 'en-US' };

// speakingId is the id of the message currently being read (or null), NOT a
// plain boolean - a shared boolean made every "Read aloud" button show "Stop"
// at once as soon as any one message started speaking.
export default function useSpeech() {
  const [speakingId, setSpeakingId] = useState(null);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setSpeakingId(null);
  }, []);

  const speak = useCallback((text, langCode = 'en', id) => {
    if (speakingId === id) {
      stop();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const targetLang = TTS_LANG[langCode] || 'en-US';
    utterance.lang = targetLang;

    const voices = window.speechSynthesis.getVoices();
    let preferredVoice = voices.find((v) => v.lang.includes(targetLang));
    if (!preferredVoice) {
      preferredVoice = voices.find((v) => v.name.includes('Google') || v.name.includes('Natural'));
    }
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(id);
    window.speechSynthesis.speak(utterance);
  }, [speakingId, stop]);

  return { speakingId, speak, stop };
}
