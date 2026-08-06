export interface DepartmentReference {
  id: string;
  name: string;
  path?: string;
  isPrimary: boolean;
}

export interface DirectoryContact {
  email?: string;
  phone?: string;
  telephone?: string;
}

export interface DirectoryUser {
  id: string;
  displayName: string;
  avatarUrl?: string;
  status: string;
  title?: string;
  employeeId?: string;
  primaryDepartment?: DepartmentReference;
  departments: DepartmentReference[];
  contacts: DirectoryContact;
}

export interface DepartmentNode {
  id: string;
  name: string;
  parentId?: string;
  path?: string;
  enabled: boolean;
  children: DepartmentNode[];
  users: DirectoryUser[];
}

export interface OrganizationTreeResponse {
  tree: DepartmentNode;
  users: {
    total: number;
    attached: number;
    unassigned: DirectoryUser[];
  };
}

export interface DirectoryMember {
  id: string;
  displayName: string;
  avatarUrl?: string;
  accountStatus?: string;
  employmentStatus?: string;
  enabled: boolean;
  departed: boolean;
  primaryDepartment?: DepartmentReference;
  departments: DepartmentReference[];
}

export interface OrganizationMembersResponse {
  items: DirectoryMember[];
  page: {
    pageSize: number;
    nextCursor?: string;
    hasMore: boolean;
    total?: number;
  };
}

export interface MembersQuery {
  departmentId?: string;
  includeSubdepartments?: boolean;
  pageSize?: number;
  cursor?: string;
}
