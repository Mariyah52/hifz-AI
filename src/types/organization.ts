export interface OrganizationAdmin {
  id: string;
  name: string;
  slug: string;
  plan: string;
  maxStudents: number;
  maxTeachers: number;
  currentStudentCount: number;
  currentTeacherCount: number;
  primaryColor: string | null;
  logoUrl: string | null;
}
