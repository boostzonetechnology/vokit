export type NotificationTemplate = {
  id?: string;
  event_type?: string;
  channel?: string;
  subject?: string;
  body?: string;
  version?: number;
};

export type NotificationDelivery = {
  id?: string;
  user_id?: string | null;
  recipient_email?: string;
  channel?: string;
  event_type?: string;
  status?: string;
  error?: string;
  created_at?: string;
};

export type InboxItem = {
  id: string;
  title?: string;
  category?: string;
  read_at?: string | null;
  created_at?: string;
  body?: string;
};

export type NotificationTab = "templates" | "deliveries" | "announcements" | "inbox";
