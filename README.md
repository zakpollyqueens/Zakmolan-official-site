This repository currently has payments and donation functionality removed.

What was removed
- Donation database and related endpoints (admin listing, donation records) have been removed from the application.
- Payment integrations (MTN, Airtel, Flutterwave) were removed in earlier commits.

What remains
- Static site pages (index, about, services, contact) and contact email sending (requires EMAIL_PASSWORD env var).
- The /donate route now redirects to home with a notice.

If you want donations or payments restored later, I can re-add a clean, sandbox-first integration for MTN/Airtel or integrate an aggregator.
