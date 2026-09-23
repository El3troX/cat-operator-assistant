import { useMutation } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'motion/react';
import { useEffect, useRef, useState } from 'react';
import { Check, FileWarning, Mic, MicOff, Send, Sparkles, Volume2, VolumeX, WifiOff, X } from 'lucide-react';
import { Badge, SeverityBadge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { api } from '../../lib/api';
import { useCreateIncident } from '../../lib/queries';
import { useSession } from '../../lib/session';
import { cn, nowLocalIso } from '../../lib/utils';
import { speak, stopSpeaking, useSpeechRecognition } from './speech';

const SUGGESTIONS = [
  "What's next?",
  'How long will trenching take in the rain?',
  'Is anyone near my machine?',
  "What's my safety score?",
  'Log it: I clipped the barrier by the east trench, nobody hurt',
];
const MAX_HISTORY = 20;

// API history: text turns only, local notes dropped, and it must start with a user turn.
function toHistory(messages) {
  const turns = messages.filter((m) => !m.local).map(({ role, content }) => ({ role, content })).slice(-MAX_HISTORY);
  while (turns.length && turns[0].role !== 'user') turns.shift();
  return turns;
}

function DraftCard({ draft, onConfirm, onDiscard, saving }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="rounded-2xl border border-warn/50 bg-warn/8 p-4"
      role="group"
      aria-label="Incident draft awaiting confirmation"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-sm font-semibold text-ink">
          <FileWarning className="size-4 text-warn" aria-hidden /> Incident draft · {draft.machine_id}
        </span>
        <SeverityBadge severity={draft.severity} />
      </div>
      <p className="mt-2 text-base text-ink">{draft.description}</p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <Button variant="ghost" size="lg" onClick={onDiscard} disabled={saving}>
          <X className="size-5" aria-hidden /> Discard
        </Button>
        <Button variant="primary" size="lg" onClick={onConfirm} loading={saving}>
          {!saving && <Check className="size-5" aria-hidden />} Confirm &amp; log
        </Button>
      </div>
    </motion.div>
  );
}

export default function Copilot() {
  const { operatorId, machineId } = useSession();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState(null);
  const [voiceOn, setVoiceOn] = useState(true);
  const [text, setText] = useState('');
  const listRef = useRef(null);
  const chat = useMutation({ mutationFn: api.copilotChat });
  const createIncident = useCreateIncident();

  const addAssistant = (content, extra = {}) => {
    setMessages((prev) => [...prev, { role: 'assistant', content, ...extra }]);
    if (voiceOn) speak(content);
  };

  const send = (raw) => {
    const content = raw.trim();
    if (!content || chat.isPending) return;
    const next = [...messages, { role: 'user', content }];
    setMessages(next);
    setText('');
    setDraft(null);
    chat.mutate(
      { operator_id: operatorId, machine_id: machineId, messages: toHistory(next) },
      {
        onSuccess: (res) => {
          addAssistant(res.reply, { actions: res.actions, source: res.source });
          setDraft(res.draft_incident);
        },
        onError: (err) => addAssistant(`Sorry, I couldn't reach the server. ${err.message}`, { local: true }),
      },
    );
  };

  const speech = useSpeechRecognition(send);

  const confirmDraft = () =>
    createIncident.mutate(
      { ...draft, timestamp: nowLocalIso() },
      {
        onSuccess: (incident) => {
          setDraft(null);
          addAssistant(`Logged incident number ${incident.id}. Your supervisor can see it now.`, { local: true });
        },
      },
    );

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, draft, chat.isPending]);

  const lastSource = [...messages].reverse().find((m) => m.source)?.source;

  if (!open) {
    return (
      <motion.button
        type="button"
        onClick={() => setOpen(true)}
        whileTap={{ scale: 0.94 }}
        className="fixed right-4 bottom-28 z-40 flex h-16 items-center gap-2 rounded-full bg-accent px-6 text-lg font-bold text-accent-ink shadow-[0_8px_30px_-6px_var(--color-accent)] cursor-pointer"
      >
        <Mic className="size-6" aria-hidden /> Co-pilot
      </motion.button>
    );
  }

  return (
    <section
      aria-label="Co-pilot"
      onKeyDown={(e) => e.key === 'Escape' && setOpen(false)}
      className="fixed inset-x-0 bottom-24 z-40 mx-auto flex max-h-[72vh] max-w-4xl flex-col px-3"
    >
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex min-h-0 flex-col overflow-hidden rounded-3xl border border-line-strong bg-surface shadow-2xl"
      >
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="size-5 text-accent" aria-hidden />
            <h2 className="text-base font-bold text-ink">Co-pilot</h2>
            {lastSource === 'claude' && <Badge tone="ok">Claude</Badge>}
            {lastSource === 'offline' && (
              <Badge tone="warn" title="No AI connection: basic voice commands only">
                <WifiOff className="size-3.5" aria-hidden /> Offline mode
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              aria-label={voiceOn ? 'Mute spoken replies' : 'Speak replies aloud'}
              aria-pressed={voiceOn}
              onClick={() => {
                if (voiceOn) stopSpeaking();
                setVoiceOn(!voiceOn);
              }}
            >
              {voiceOn ? <Volume2 className="size-5" aria-hidden /> : <VolumeX className="size-5" aria-hidden />}
            </Button>
            <Button variant="ghost" size="icon" aria-label="Close co-pilot" onClick={() => setOpen(false)}>
              <X className="size-5" aria-hidden />
            </Button>
          </div>
        </header>

        <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-4" aria-live="polite">
          {messages.length === 0 && (
            <div>
              <p className="text-sm text-muted">Tap the mic and talk, or try one of these:</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => send(s)}
                    className="rounded-full border border-line bg-surface-2 px-4 py-2 text-left text-sm font-medium text-ink transition hover:border-accent/50 hover:text-accent cursor-pointer"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={cn('flex', m.role === 'user' ? 'justify-end' : 'justify-start')}>
              <div
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-2.5 text-base',
                  m.role === 'user' ? 'rounded-br-md bg-accent text-accent-ink' : 'rounded-bl-md bg-surface-2 text-ink',
                )}
              >
                {m.content}
                {m.actions?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.actions.map((a, j) => (
                      <Badge key={j} tone="info">
                        {a.summary}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {chat.isPending && (
            <div className="flex gap-1.5 px-2 py-3" aria-label="Co-pilot is thinking">
              {[0, 1, 2].map((d) => (
                <motion.span
                  key={d}
                  className="size-2 rounded-full bg-muted"
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1, repeat: Infinity, delay: d * 0.2 }}
                />
              ))}
            </div>
          )}

          <AnimatePresence>
            {draft && (
              <DraftCard
                draft={draft}
                saving={createIncident.isPending}
                onConfirm={confirmDraft}
                onDiscard={() => {
                  setDraft(null);
                  addAssistant('Discarded. Nothing was logged.', { local: true });
                }}
              />
            )}
          </AnimatePresence>
        </div>

        <footer className="border-t border-line px-4 py-3">
          {(speech.listening || speech.error) && (
            <p className={cn('mb-2 px-1 text-sm', speech.error ? 'text-danger' : 'text-muted')} role="status">
              {speech.error ?? (speech.interim || 'Listening…')}
            </p>
          )}
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(text);
            }}
          >
            {speech.supported && (
              <motion.button
                type="button"
                onClick={speech.listening ? speech.stop : speech.start}
                aria-label={speech.listening ? 'Stop listening' : 'Talk to co-pilot'}
                aria-pressed={speech.listening}
                animate={speech.listening ? { scale: [1, 1.08, 1] } : { scale: 1 }}
                transition={speech.listening ? { duration: 1, repeat: Infinity } : undefined}
                className={cn(
                  'grid size-16 shrink-0 place-items-center rounded-full cursor-pointer',
                  speech.listening ? 'bg-danger text-white' : 'bg-accent text-accent-ink',
                )}
              >
                {speech.listening ? <MicOff className="size-7" aria-hidden /> : <Mic className="size-7" aria-hidden />}
              </motion.button>
            )}
            <label className="sr-only" htmlFor="copilot-input">
              Message the co-pilot
            </label>
            <input
              id="copilot-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={speech.supported ? 'Or type a message…' : 'Type a message…'}
              autoComplete="off"
              className="h-14 min-w-0 flex-1 rounded-xl border border-line bg-surface-2 px-4 text-base text-ink placeholder:text-faint focus:border-accent focus:outline-none"
            />
            <Button type="submit" variant="secondary" size="icon" className="size-14 shrink-0" aria-label="Send" disabled={!text.trim() || chat.isPending}>
              <Send className="size-5" aria-hidden />
            </Button>
          </form>
        </footer>
      </motion.div>
    </section>
  );
}
