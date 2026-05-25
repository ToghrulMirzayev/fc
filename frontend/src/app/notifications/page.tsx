import { ComingSoon } from "@/components/ComingSoon";

export default function NotificationsPage() {
  return (
    <ComingSoon
      crumbs={["Settings", "Notifications"]}
      title="Notifications"
      headline="Custom notifications are coming."
      description="Customize the templates members receive — expiration warnings, freeze reminders, and renewal nudges via Telegram and email."
    />
  );
}
