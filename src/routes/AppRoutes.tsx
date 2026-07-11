import { Routes, Route, Outlet } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { RequireAuth } from '@/components/auth/RequireAuth';
import { RequireRole } from '@/components/auth/RequireRole';
import { useOrganizationTheme } from '@/hooks/useOrganizationTheme';
import { LoginPage } from '@/pages/LoginPage';
import { ForgotPasswordPage } from '@/pages/ForgotPasswordPage';
import { ResetPasswordPage } from '@/pages/ResetPasswordPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { LearnPage } from '@/pages/LearnPage';
import { LearnSurahPage } from '@/pages/LearnSurahPage';
import { MushafPage } from '@/pages/MushafPage';
import { PracticePage } from '@/pages/PracticePage';
import { PracticeSurahPage } from '@/pages/PracticeSurahPage';
import { TestPage } from '@/pages/TestPage';
import { TestSurahPage } from '@/pages/TestSurahPage';
import { ProgressPage } from '@/pages/ProgressPage';
import { RevisionPage } from '@/pages/RevisionPage';
import { LeaderboardPage } from '@/pages/LeaderboardPage';
import { AdvancedAnalyticsPage } from '@/pages/AdvancedAnalyticsPage';
import { TestModesPage } from '@/pages/TestModesPage';
import { TestModeRunnerPage } from '@/pages/TestModeRunnerPage';
import { VisualMemorizationPage } from '@/pages/VisualMemorizationPage';
import { AssistantPage } from '@/pages/AssistantPage';
import { NotesPage } from '@/pages/NotesPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { MessagesPage } from '@/pages/MessagesPage';
import { ConversationPage } from '@/pages/ConversationPage';
import { ClassUpdatesPage } from '@/pages/ClassUpdatesPage';
import { TeacherClassUpdatesPage } from '@/pages/portals/teacher/TeacherClassUpdatesPage';
import { TeacherDashboardPage } from '@/pages/portals/teacher/TeacherDashboardPage';
import { LiveSessionHostPage } from '@/pages/portals/teacher/LiveSessionHostPage';
import { LiveSessionJoinPage } from '@/pages/LiveSessionJoinPage';
import { CertificatesPage } from '@/pages/CertificatesPage';
import { TeacherStudentDetailPage } from '@/pages/portals/teacher/TeacherStudentDetailPage';
import { ParentDashboardPage } from '@/pages/portals/parent/ParentDashboardPage';
import { AdminDashboardPage } from '@/pages/portals/admin/AdminDashboardPage';
import { MarketplacePage } from '@/pages/portals/admin/MarketplacePage';
import { DeveloperApiPage } from '@/pages/portals/admin/DeveloperApiPage';

/** Wraps every authenticated route in the shared shell (bottom nav for students, bare header otherwise). */
function AppShellLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

/**
 * Real, role-based routing as of Phase 10 — replaces the old always-open
 * `/portals` hub. Each role logs into its own account and lands directly
 * on its own screen; `RequireRole` bounces anyone who navigates outside
 * their role back to their own home instead of showing them another
 * account's data.
 */
export function AppRoutes() {
  // Applies the logged-in user's organization branding (if any theme is
  // installed) as CSS variables app-wide — see the hook's own comment.
  useOrganizationTheme();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route element={<RequireAuth />}>
        <Route element={<AppShellLayout />}>
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/messages/:conversationId" element={<ConversationPage />} />
          <Route path="/class-updates" element={<ClassUpdatesPage />} />

          <Route element={<RequireRole role="student" />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/learn" element={<LearnPage />} />
            <Route path="/learn/:surahNumber" element={<LearnSurahPage />} />
            <Route path="/mushaf/:pageNumber" element={<MushafPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/practice/:surahNumber" element={<PracticeSurahPage />} />
            <Route path="/test" element={<TestPage />} />
            <Route path="/test/:surahNumber" element={<TestSurahPage />} />
            <Route path="/progress" element={<ProgressPage />} />
            <Route path="/revision" element={<RevisionPage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/analytics" element={<AdvancedAnalyticsPage />} />
            <Route path="/test-modes" element={<TestModesPage />} />
            <Route path="/test-modes/:mode" element={<TestModeRunnerPage />} />
            <Route path="/memorize/:pageNumber" element={<VisualMemorizationPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/notes" element={<NotesPage />} />
            <Route path="/live-session" element={<LiveSessionJoinPage />} />
            <Route path="/certificates" element={<CertificatesPage />} />
          </Route>

          <Route element={<RequireRole role="teacher" />}>
            <Route path="/teacher" element={<TeacherDashboardPage />} />
            <Route path="/teacher/:studentId" element={<TeacherStudentDetailPage />} />
            <Route path="/teacher/live-session" element={<LiveSessionHostPage />} />
            <Route path="/teacher/class-updates" element={<TeacherClassUpdatesPage />} />
          </Route>

          <Route element={<RequireRole role="parent" />}>
            <Route path="/parent" element={<ParentDashboardPage />} />
          </Route>

          <Route element={<RequireRole role="admin" />}>
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/marketplace" element={<MarketplacePage />} />
            <Route path="/admin/developer-api" element={<DeveloperApiPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
