import { useState } from 'react';
import { Check, X } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { submitQuizTestSession } from '@/services/testService';
import type { GeneratedQuestion } from '@/types/testModes';

interface MultipleChoiceRunnerProps {
  question: GeneratedQuestion;
  onFinish: () => void;
}

const ARABIC_RE = /[\u0600-\u06FF]/;

function ChoiceLabel({ text }: { text: string }) {
  if (ARABIC_RE.test(text)) {
    return (
      <span className="font-arabic text-lg" dir="rtl">
        {text}
      </span>
    );
  }
  if (/^\d+$/.test(text)) {
    return <span className="font-mono text-base">Page {text}</span>;
  }
  return <span className="font-body text-sm">{text}</span>;
}

export function MultipleChoiceRunner({ question, onFinish }: MultipleChoiceRunnerProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const isAnswered = selected !== null;
  const isCorrect = selected === question.correctChoiceIndex;

  function handleSelect(index: number) {
    if (isAnswered) return;
    setSelected(index);
  }

  async function handleContinue() {
    setIsSaving(true);
    try {
      await submitQuizTestSession({
        surahNumber: question.surahNumber,
        surahName: question.surahName,
        fromAyah: question.fromAyah,
        toAyah: question.toAyah,
        isCorrect,
      });
    } finally {
      setIsSaving(false);
      onFinish();
    }
  }

  return (
    <Card className="flex flex-col gap-4">
      <p className="font-body text-sm text-ink whitespace-pre-line">{question.prompt}</p>

      <div className="flex flex-col gap-2">
        {question.choices?.map((choice, index) => {
          const isThisCorrect = index === question.correctChoiceIndex;
          const isThisSelected = index === selected;

          let tone = 'bg-paper-dim text-ink';
          if (isAnswered && isThisCorrect) tone = 'bg-teal/15 text-teal-dark border border-teal/40';
          else if (isAnswered && isThisSelected) tone = 'bg-maroon/10 text-maroon border border-maroon/30';

          return (
            <button
              key={index}
              onClick={() => handleSelect(index)}
              disabled={isAnswered}
              className={`flex items-center justify-between gap-2 rounded-2xl px-4 py-3 text-left transition-colors ${tone}`}
            >
              <ChoiceLabel text={choice} />
              {isAnswered && isThisCorrect && <Check size={16} className="shrink-0 text-teal-dark" />}
              {isAnswered && isThisSelected && !isThisCorrect && <X size={16} className="shrink-0 text-maroon" />}
            </button>
          );
        })}
      </div>

      {isAnswered && (
        <button
          onClick={handleContinue}
          disabled={isSaving}
          className="rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors disabled:opacity-60"
        >
          {isSaving ? 'Saving…' : 'Continue'}
        </button>
      )}
    </Card>
  );
}
