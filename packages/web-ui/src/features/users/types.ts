export type PlatformUser = {
  id: string;
  membership_id?: string;
  email?: string;
  principal_type?: string;
  role?: string;
  tenant_id?: string | null;
  customer_id?: string | null;
  status?: string;
};

export type PlatformInvitation = {
  id: string;
  email?: string;
  principal_type?: string;
  role?: string;
  tenant_id?: string | null;
  customer_id?: string | null;
  status?: string;
  token?: string;
};
