export interface CurrentUser {
  id: string;
  displayName: string;
  permissions: string[];
}

export interface AppInitialState {
  currentUser: CurrentUser | null;
}
