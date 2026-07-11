export interface ConversationSummary {
  id: string;
  otherUserId: string;
  otherUserName: string;
  otherUserRole: string;
  lastMessagePreview: string | null;
  lastMessageAt: string | null;
  unreadCount: number;
}

export interface DirectMessage {
  id: string;
  senderUserId: string;
  content: string | null;
  attachmentUrl: string | null;
  attachmentType: 'audio' | 'file' | null;
  createdAt: string;
  readAt: string | null;
}

export interface Announcement {
  id: string;
  classId: string | null;
  className: string | null;
  authorName: string;
  title: string;
  content: string;
  createdAt: string;
}

export interface Homework {
  id: string;
  classId: string;
  className: string;
  title: string;
  description: string;
  dueDate: string;
  createdAt: string;
}
