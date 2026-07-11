import { Download, Loader2, Trash2 } from 'lucide-react';
import { useSurahDownload } from '@/hooks/useSurahDownload';

interface DownloadButtonProps {
  surahNumber: number;
  ayahCount: number;
}

export function DownloadButton({ surahNumber, ayahCount }: DownloadButtonProps) {
  const { isDownloaded, isDownloading, progress, error, download, remove } = useSurahDownload(
    surahNumber,
    ayahCount,
  );

  if (isDownloading && progress) {
    const percent = Math.round((progress.completed / progress.total) * 100);
    return (
      <div className="flex items-center gap-2 text-xs text-ink-soft font-body">
        <Loader2 size={14} className="animate-spin" />
        Downloading… {percent}%
      </div>
    );
  }

  if (isDownloaded) {
    return (
      <button
        onClick={remove}
        className="flex items-center gap-1.5 rounded-full bg-teal/10 text-teal-dark px-3 py-1.5
          text-xs font-semibold font-body hover:bg-maroon/10 hover:text-maroon transition-colors"
      >
        <Trash2 size={13} />
        Downloaded — remove
      </button>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={download}
        className="flex items-center gap-1.5 rounded-full bg-sage text-ink-soft px-3 py-1.5
          text-xs font-semibold font-body hover:bg-[#d8dfcd] transition-colors"
      >
        <Download size={13} />
        Download for offline
      </button>
      {error && <p className="text-[11px] text-maroon font-body">{error}</p>}
    </div>
  );
}
