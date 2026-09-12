export type IntegrationProvider = {
  provider?: string;
  category?: string;
};

export type IntegrationConnection = {
  id: string;
  agency_id?: string;
  customer_id?: string;
  provider?: string;
  status?: string;
  display_name?: string;
  has_secret?: boolean;
};
