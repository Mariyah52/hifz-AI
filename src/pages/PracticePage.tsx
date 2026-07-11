import { Link } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useSurahList } from '@/hooks/useQuranData';

export function PracticePage() {
  const surahs = useSurahList();

  return (
    <>
      <Header greeting="Practice" name={`${surahs.length} surahs`} />
      <main className="px-5 mt-2">
        <Card className="mb-4 py-4 text-center">
          <p className="font-body text-sm text-ink-soft">
            Pick a surah to record yourself reciting a range of ayahs and review the playback.
          </p>
        </Card>
        <div className="flex flex-col gap-2 pb-4">
          {surahs.map((surah) => (
            <Link
              key={surah.number}
              to={`/practice/${surah.number}`}
              className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-teal/10 font-mono text-xs font-semibold text-teal-dark">
                  {surah.number}
                </span>
                <div>
                  <p className="font-body font-semibold text-ink text-sm">{surah.name}</p>
                  <p className="font-arabic text-sm text-ink-soft" dir="rtl">
                    {surah.arabicName}
                  </p>
                </div>
              </div>
              <Badge tone={surah.revelationType === 'meccan' ? 'gold' : 'teal'}>
                {surah.ayahCount} ayahs
              </Badge>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
