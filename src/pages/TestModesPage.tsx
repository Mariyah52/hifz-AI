import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { TEST_MODE_DESCRIPTORS } from '@/types/testModes';

export function TestModesPage() {
  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/test"
          aria-label="Back to Test"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Test Mode</p>
          <h1 className="heading-section">Advanced modes</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4">
        <Card className="mb-4 py-4 text-center">
          <p className="font-body text-sm text-ink-soft">
            Every mode below draws from your own completed Sabaqs — pick one to generate a real
            question.
          </p>
        </Card>

        <div className="flex flex-col gap-2">
          {TEST_MODE_DESCRIPTORS.map((descriptor) => (
            <Link
              key={descriptor.mode}
              to={`/test-modes/${descriptor.mode}`}
              className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
            >
              <div>
                <p className="font-body font-semibold text-ink text-sm">{descriptor.label}</p>
                <p className="font-body text-xs text-ink-soft mt-0.5">{descriptor.description}</p>
              </div>
              <ChevronRight size={16} className="text-ink-soft shrink-0" />
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
