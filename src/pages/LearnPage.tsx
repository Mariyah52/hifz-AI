import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, BookOpen, Eye } from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useSurahList } from '@/hooks/useQuranData';
import { getDownloadedSurahNumbers } from '@/services/audioCacheService';

export function LearnPage() {
  const surahs = useSurahList();
  const [downloadedSurahs, setDownloadedSurahs] = useState<Set<number>>(new Set());

  useEffect(() => {
    getDownloadedSurahNumbers().then((numbers) => setDownloadedSurahs(new Set(numbers)));
  }, []);

  return (
    <>
      <Header greeting="Learn" name={`${surahs.length} surahs`} />
      <main className="px-5 mt-2">
        <Card className="mb-4 py-4 text-center">
          <p className="font-body text-sm text-ink-soft">
            Tap a surah to open its Mushaf view with Al-Husary recitation and repeat modes.
          </p>
        </Card>

        <Link
          to="/mushaf/1"
          className="flex items-center justify-between rounded-2xl bg-teal/10 px-4 py-3 mb-4
            hover:bg-teal/20 transition-colors"
        >
          <div>
            <p className="font-body font-semibold text-teal-dark text-sm">Browse by page</p>
            <p className="font-body text-xs text-ink-soft mt-0.5">
              604-page Mushaf view — memorize page by page instead of by surah
            </p>
          </div>
          <BookOpen size={20} className="text-teal-dark" />
        </Link>
        <Link
          to="/memorize/1"
          className="flex items-center justify-between rounded-2xl bg-gold/10 px-4 py-3 mb-4
            hover:bg-gold/20 transition-colors"
        >
          <div>
            <p className="font-body font-semibold text-[#8a6218] text-sm">Visual memorization</p>
            <p className="font-body text-xs text-ink-soft mt-0.5">
              Hide a word, a line, a half page — recall it, tap to reveal
            </p>
          </div>
          <Eye size={20} className="text-[#8a6218]" />
        </Link>
        <div className="flex flex-col gap-2 pb-4">
          {surahs.map((surah) => (
            <Link
              key={surah.number}
              to={`/learn/${surah.number}`}
              className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-teal/10 font-mono text-xs font-semibold text-teal-dark">
                  {surah.number}
                </span>
                <div>
                  <p className="font-body font-semibold text-ink text-sm flex items-center gap-1.5">
                    {surah.name}
                    {downloadedSurahs.has(surah.number) && (
                      <Download size={12} className="text-teal-dark" aria-label="Downloaded for offline" />
                    )}
                  </p>
                  <p className="font-arabic text-sm text-ink-soft" dir="rtl">
                    {surah.arabicName}
                  </p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <span className="font-mono text-xs text-ink-soft">{surah.ayahCount} ayahs</span>
                <Badge tone={surah.revelationType === 'meccan' ? 'gold' : 'teal'}>
                  {surah.revelationType}
                </Badge>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
