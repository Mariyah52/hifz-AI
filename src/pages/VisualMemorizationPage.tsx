import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, RotateCcw, Eye } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { MushafPageNav } from '@/components/mushaf/MushafPageNav';
import { WordMaskedPageViewer, type HideLevel } from '@/components/mushaf/WordMaskedPageViewer';
import { HideLevelSelector } from '@/components/mushaf/HideLevelSelector';
import { useMushafPage } from '@/hooks/useMushafPage';

export function VisualMemorizationPage() {
  const params = useParams<{ pageNumber: string }>();
  const navigate = useNavigate();
  const requestedPage = Number(params.pageNumber) || 1;

  const { pageNumber, ayahs, error, isLoading, totalPages, goToPage, nextPage, prevPage } =
    useMushafPage(requestedPage);

  const [hideLevel, setHideLevel] = useState<HideLevel>('word');
  // Random on every mount (fresh page load / navigation), not a fixed
  // literal — otherwise mulberry32(seed) deterministically masks the same
  // word every single time until the user manually taps "New mask".
  const [maskSeed, setMaskSeed] = useState(() => Math.floor(Math.random() * 1_000_000));

  function syncRoute(page: number) {
    navigate(`/memorize/${page}`, { replace: true });
  }

  function newMask() {
    setMaskSeed((s) => s + 1);
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/learn"
          aria-label="Back to Learn"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Visual memorization</p>
          <h1 className="heading-section">Page {pageNumber}</h1>
        </div>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        <Card className="py-3">
          <p className="font-body text-xs text-ink-soft text-center">
            Tap a blurred word to reveal it. "Line" hiding follows how the text wraps on your
            screen right now, not a fixed printed page — see the note below for why.
          </p>
        </Card>

        <MushafPageNav
          pageNumber={pageNumber}
          totalPages={totalPages}
          onPrev={() => {
            prevPage();
            syncRoute(Math.max(1, pageNumber - 1));
          }}
          onNext={() => {
            nextPage();
            syncRoute(Math.min(totalPages, pageNumber + 1));
          }}
          onGoToPage={(page) => {
            goToPage(page);
            syncRoute(Math.min(totalPages, Math.max(1, page)));
          }}
        />

        <div className="flex items-center justify-between gap-3">
          <HideLevelSelector value={hideLevel} onChange={(level) => { setHideLevel(level); setMaskSeed((s) => s + 1); }} />
        </div>

        <div className="flex gap-2">
          <button
            onClick={newMask}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-full bg-sage text-ink-soft px-3 py-2 text-xs font-semibold font-body hover:bg-[#d8dfcd] transition-colors"
          >
            <RotateCcw size={13} />
            New mask
          </button>
          <button
            onClick={() => setHideLevel('fullPage')}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-full bg-sage text-ink-soft px-3 py-2 text-xs font-semibold font-body hover:bg-[#d8dfcd] transition-colors"
          >
            <Eye size={13} />
            Hide everything
          </button>
        </div>

        {error && (
          <Card className="text-center py-6">
            <p className="font-body text-sm text-ink-soft">
              Couldn't load this page right now. Check your connection and try again.
            </p>
          </Card>
        )}

        {isLoading && !error && (
          <Card className="text-center py-10">
            <p className="font-body text-sm text-ink-soft">Loading page…</p>
          </Card>
        )}

        {ayahs && <WordMaskedPageViewer ayahs={ayahs} hideLevel={hideLevel} maskSeed={maskSeed} />}
      </main>
    </>
  );
}
