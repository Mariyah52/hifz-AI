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
  secondaryColor: string | null;
  logoUrl: string | null;
  welcomeMessage: string | null;
  principalMessage: string | null;
}

export interface UpdateOrganizationRequest {
  name?: string;
  primaryColor?: string;
  secondaryColor?: string;
  logoUrl?: string;
  welcomeMessage?: string;
  principalMessage?: string;
}
