export interface LiveCoachMistake {
  position: number;
  mistakeType: string;
  ayahNumber: number;
  referenceWord: string;
  transcribedWord: string;
}

export interface LiveCoachStartedMessage {
  type: 'started';
  totalReferenceWordCount: number;
}

export interface LiveCoachChunkResultMessage {
  type: 'chunk_result';
  chunkNumber: number;
  matchedWordCount: number;
  totalReferenceWordCount: number;
  mistakes: LiveCoachMistake[];
  chunkTranscriptionError: string | null;
}

export interface LiveCoachErrorMessage {
  type: 'error';
  message: string;
}
