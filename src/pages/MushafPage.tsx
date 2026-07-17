import { Link, useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, Palette } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { MushafPageViewer } from '@/components/mushaf/MushafPageViewer';
import { MushafPageNav } from '@/components/mushaf/MushafPageNav';
import { TajweedLegend } from '@/components/mushaf/TajweedLegend';
import { useMushafPage } from '@/hooks/useMushafPage';

export function MushafPage() {
  const params = useParams<{ pageNumber: string }>();
  const navigate = useNavigate();
  const requestedPage = Number(params.pageNumber) || 1;

  const {
    pageNumber,
    ayahs,
    error,
    isLoading,
    totalPages,
    goToPage,
    nextPage,
    prevPage,
    showTajweed,
    setShowTajweed,
    tajweedAyahs,
    isTajweedLoading,
    tajweedError,
  } = useMushafPage(requestedPage);

  function syncRoute(page: number) {
    navigate(`/mushaf/${page}`, { replace: true });
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
        <div className="flex-1">
          <p className="text-sm text-ink-soft font-body">Mushaf</p>
          <h1 className="heading-section">Page {pageNumber}</h1>
        </div>
        <button
          onClick={() => setShowTajweed((v) => !v)}
          aria-pressed={showTajweed}
          aria-label="Toggle tajweed colors"
          className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-body font-semibold transition-colors ${
            showTajweed ? 'bg-teal text-paper' : 'bg-sage text-ink-soft hover:bg-[#d8dfcd]'
          }`}
        >
          <Palette size={14} />
          Tajweed
        </button>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
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

        {showTajweed && isTajweedLoading && (
          <p className="text-center font-mono text-xs text-ink-soft">Loading tajweed colors…</p>
        )}
        {showTajweed && tajweedError && (
          <p className="text-center font-body text-xs text-maroon">{tajweedError}</p>
        )}

        {ayahs && <MushafPageViewer ayahs={ayahs} tajweedAyahs={showTajweed ? tajweedAyahs : null} />}

        {showTajweed && tajweedAyahs && <TajweedLegend />}
      </main>
    </>
  );
}
