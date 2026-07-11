import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Award, Download } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { getMyCertificates, downloadCertificatePdf } from '@/services/certificateService';
import type { Certificate } from '@/types/certificate';

export function CertificatesPage() {
  const [certificates, setCertificates] = useState<Certificate[] | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    getMyCertificates().then(setCertificates);
  }, []);

  async function handleDownload(cert: Certificate) {
    setDownloadingId(cert.id);
    try {
      await downloadCertificatePdf(cert.id, cert.title.replace(/[^\w\- ]/g, ''));
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/progress"
          aria-label="Back to Progress"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Progress</p>
          <h1 className="font-display text-xl font-semibold text-ink">Certificates</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-3">
        {certificates === null && <p className="text-center text-ink-soft font-body text-sm py-8">Loading…</p>}

        {certificates?.length === 0 && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">
              Complete a surah or juz, or earn one from your teacher, to see it here.
            </p>
          </Card>
        )}

        {certificates?.map((cert) => (
          <Card key={cert.id} className="flex items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gold/15 text-[#8a6218]">
              <Award size={18} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-body font-semibold text-ink text-sm truncate">{cert.title}</p>
              <p className="font-body text-xs text-ink-soft mt-0.5">{cert.detail}</p>
              {cert.issuedByTeacherName && (
                <p className="font-mono text-[10px] text-ink-soft mt-0.5">Issued by {cert.issuedByTeacherName}</p>
              )}
            </div>
            <button
              onClick={() => handleDownload(cert)}
              disabled={downloadingId === cert.id}
              aria-label="Download PDF"
              className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors disabled:opacity-50"
            >
              <Download size={15} />
            </button>
          </Card>
        ))}
      </main>
    </>
  );
}
