import { ComingSoon } from "@/components/ComingSoon";
import { FeatureGate } from "@/components/FeatureGate";

export default function NotificationsPage() {
  return (
    <FeatureGate feature="telegram_automation">
      <ComingSoon
        crumbs={["Settings", "Notifications"]}
        title="Notifications"
        headline="Custom notifications are coming."
        description="Customize the templates members receive — expiration warnings, freeze reminders, and renewal nudges via Telegram and email."
      />
    </FeatureGate>
  );
}
