export interface Achievement {
  key: string;
  name: string;
  description: string;
  earnedAt: string | null; // ISO datetime, null only for locked achievements
}

export interface GamificationSummary {
  xp: number;
  level: number;
  xpIntoLevel: number;
  xpToNextLevel: number;
  earnedAchievements: Achievement[];
  lockedAchievements: Achievement[];
}

export type LeaderboardScope = 'class' | 'all';

export interface LeaderboardEntry {
  rank: number;
  studentId: string;
  name: string;
  xp: number;
  level: number;
  isCurrentStudent: boolean;
}
