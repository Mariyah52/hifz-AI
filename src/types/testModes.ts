export type TestMode =
  | 'continue_next_ayah'
  | 'continue_next_page'
  | 'continue_after_random_stop'
  | 'first_ayah_recognition'
  | 'last_ayah_recognition'
  | 'match_page'
  | 'match_surah'
  | 'random_ayah'
  | 'audio_question'
  | 'page_recall'
  | 'masked_page'
  | 'mixed_revision';

export type InteractionType = 'recite' | 'multiple_choice';

/**
 * Every question here is built from real completed Sabaqs and real ayah/
 * page/surah data — never an invented range. For multiple_choice
 * questions, `correctChoiceIndex` is included immediately: like the rest
 * of Test Mode, this is a self-study tool, not a proctored exam.
 */
export interface GeneratedQuestion {
  mode: TestMode;
  interactionType: InteractionType;
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  prompt: string;
  choices: string[] | null;
  correctChoiceIndex: number | null;
  audioFirst: boolean;
}

export interface GeneratedTest {
  questions: GeneratedQuestion[];
}

export interface TestModeDescriptor {
  mode: TestMode;
  label: string;
  description: string;
}

export const TEST_MODE_DESCRIPTORS: TestModeDescriptor[] = [
  { mode: 'continue_next_ayah', label: 'Continue next ayah', description: 'The classic flow: recite a Sabaq from its start.' },
  { mode: 'continue_next_page', label: 'Continue next page', description: 'Recite the whole page a Sabaq falls on.' },
  { mode: 'continue_after_random_stop', label: 'Random stop, continue', description: 'Pick up from a random point and keep going.' },
  { mode: 'first_ayah_recognition', label: 'First ayah recognition', description: "Identify a surah's opening ayah." },
  { mode: 'last_ayah_recognition', label: 'Last ayah recognition', description: "Identify a surah's closing ayah." },
  { mode: 'match_page', label: 'Match page', description: 'Given an ayah, name the page it\u2019s on.' },
  { mode: 'match_surah', label: 'Match surah', description: 'Given an ayah with no label, name its surah.' },
  { mode: 'random_ayah', label: 'Random ayah', description: 'Recite a single randomly chosen ayah.' },
  { mode: 'audio_question', label: 'Audio question', description: 'Listen first, then continue reciting.' },
  { mode: 'page_recall', label: 'Page recall', description: 'Recall an entire page from memory.' },
  { mode: 'masked_page', label: 'Masked page', description: 'Recite the one hidden ayah in a page.' },
  { mode: 'mixed_revision', label: 'Mixed revision', description: 'A short varied session across several Sabaqs.' },
];
