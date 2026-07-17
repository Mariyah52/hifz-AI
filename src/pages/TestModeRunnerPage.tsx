import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { TestRunner } from '@/components/test/TestRunner';
import { MultipleChoiceRunner } from '@/components/test/MultipleChoiceRunner';
import { generateTest } from '@/services/testModeService';
import { TEST_MODE_DESCRIPTORS } from '@/types/testModes';
import type { GeneratedQuestion, TestMode } from '@/types/testModes';
import type { TestSession } from '@/types/test';

export function TestModeRunnerPage() {
  const params = useParams<{ mode: string }>();
  const mode = params.mode as TestMode;
  const descriptor = TEST_MODE_DESCRIPTORS.find((d) => d.mode === mode);

  const [questions, setQuestions] = useState<GeneratedQuestion[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    setQuestions(null);
    setError(null);
    setIndex(0);
    setIsDone(false);
    generateTest(mode)
      .then((result) => setQuestions(result.questions))
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not generate a question.'));
  }, [mode]);

  function goToNext() {
    if (!questions) return;
    if (index + 1 < questions.length) {
      setIndex(index + 1);
    } else {
      setIsDone(true);
    }
  }

  function handleReciteFinish(_session: TestSession) {
    // TestRunner already uploaded and saved this session internally
    // (see useTestSession/submitTestSession) — nothing left to persist here.
    goToNext();
  }

  const currentQuestion = questions?.[index];

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/test-modes"
          aria-label="Back to test modes"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Test Mode</p>
          <h1 className="heading-section">{descriptor?.label ?? mode}</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        {questions && questions.length > 1 && !isDone && (
          <p className="text-center font-mono text-xs text-ink-soft">
            Question {index + 1} of {questions.length}
          </p>
        )}

        {error && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">{error}</p>
          </Card>
        )}

        {!error && !questions && (
          <Card className="text-center py-10">
            <p className="font-body text-sm text-ink-soft">Generating a question…</p>
          </Card>
        )}

        {isDone && (
          <Card className="text-center py-8">
            <p className="font-body font-semibold text-ink text-sm mb-2">Session complete.</p>
            <Link
              to="/test-modes"
              className="inline-block rounded-full bg-teal text-paper font-semibold text-sm px-5 py-2.5 hover:bg-teal-dark transition-colors"
            >
              Try another mode
            </Link>
          </Card>
        )}

        {currentQuestion && !isDone && currentQuestion.interactionType === 'recite' && (
          <>
            <Card className="py-3">
              <p className="font-body text-xs text-ink-soft text-center">{currentQuestion.prompt}</p>
            </Card>
            <TestRunner
              key={index}
              surahNumber={currentQuestion.surahNumber}
              surahName={currentQuestion.surahName}
              fromAyah={currentQuestion.fromAyah}
              toAyah={currentQuestion.toAyah}
              onFinish={handleReciteFinish}
            />
          </>
        )}

        {currentQuestion && !isDone && currentQuestion.interactionType === 'multiple_choice' && (
          <MultipleChoiceRunner key={index} question={currentQuestion} onFinish={goToNext} />
        )}
      </main>
    </>
  );
}
