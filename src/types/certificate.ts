export type CertificateType = 'surah_completion' | 'juz_completion' | 'attendance' | 'competition';

export interface Certificate {
  id: string;
  type: CertificateType;
  title: string;
  detail: string;
  issuedByTeacherName: string | null;
  issuedAt: string;
}
