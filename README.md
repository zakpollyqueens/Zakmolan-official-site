I removed payment-related endpoints and files from the application and replaced the payments frontend/script with a no-op.

What I removed/disabled:
- All /payments/* and /momo/* endpoints (create/verify/webhook) have been removed from app.py.
- static/payments.js replaced with a stub.
- templates/payments_return.html replaced with a notice page.

Notes:
- The donations DB and admin endpoints remain available so historical donation records are preserved and accessible via the admin endpoints (protected by ADMIN_KEY).
- If you want the files fully deleted from the repo history instead of stubbed, I can open a PR with file deletions or walk you through removing them via the GitHub UI.
