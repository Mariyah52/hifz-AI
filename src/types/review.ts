import type { Sabaq } from './lesson';

export interface ReviewSchedule {
  repetitionNumber: number;
  easeFactor: number;
  intervalDays: number;
  dueDate: string; // ISO date
  lastReviewedDate: string | null;
}

export interface DueReview {
  sabaq: Sabaq;
  schedule: ReviewSchedule;
}
