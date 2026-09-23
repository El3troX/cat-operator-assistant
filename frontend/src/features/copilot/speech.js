import { useCallback, useEffect, useRef, useState } from 'react';

const Recognition = typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : undefined;

// Tap to talk: one utterance per start(); the browser ends it on silence.
export function useSpeechRecognition(onFinal) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState('');
  const [error, setError] = useState(null);
  const recognition = useRef(null);
  const onFinalRef = useRef(onFinal);

  useEffect(() => {
    onFinalRef.current = onFinal;
  }, [onFinal]);

  const start = useCallback(() => {
    if (!Recognition || recognition.current) return;
    const rec = new Recognition();
    rec.lang = navigator.language || 'en-US';
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (event) => {
      const transcript = Array.from(event.results, (r) => r[0].transcript).join('');
      setInterim(transcript);
      if (event.results[event.results.length - 1].isFinal && transcript.trim()) onFinalRef.current(transcript.trim());
    };
    rec.onerror = (event) => setError(event.error === 'not-allowed' ? 'Microphone access was blocked.' : `Voice input failed (${event.error}).`);
    rec.onend = () => {
      recognition.current = null;
      setListening(false);
      setInterim('');
    };
    setError(null);
    recognition.current = rec;
    rec.start();
    setListening(true);
  }, []);

  const stop = useCallback(() => recognition.current?.stop(), []);

  useEffect(() => () => recognition.current?.abort(), []);

  return { supported: Boolean(Recognition), listening, interim, error, start, stop };
}

export function speak(text) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  window.speechSynthesis.speak(utterance);
}

export function stopSpeaking() {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
}
