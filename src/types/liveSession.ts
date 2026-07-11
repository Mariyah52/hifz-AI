export type LiveSessionStatus = 'scheduled' | 'live' | 'ended';
export type MarkType = 'perfect' | 'hesitation' | 'mistake';
export type PeerRole = 'teacher' | 'student';

export interface LiveSession {
  id: string;
  classId: string;
  className: string;
  teacherName: string;
  status: LiveSessionStatus;
  startedAt: string;
  endedAt: string | null;
}

export interface LiveSessionParticipant {
  studentId: string;
  studentName: string;
  joinedAt: string;
  leftAt: string | null;
  durationSeconds: number | null;
}

export interface LiveSessionMistake {
  studentId: string;
  studentName: string;
  markType: MarkType;
  note: string | null;
  createdAt: string;
}

export interface LiveSessionReport {
  session: LiveSession;
  participants: LiveSessionParticipant[];
  mistakes: LiveSessionMistake[];
}

export interface RemotePeer {
  peerId: string;
  role: PeerRole;
  name: string;
  connectionState: RTCPeerConnectionState;
}

export interface LiveMistakeEvent {
  studentPeerId: string;
  markType: MarkType;
  note: string | null;
  at: number;
}
