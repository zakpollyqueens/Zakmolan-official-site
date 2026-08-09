Sandbox setup for MTN & Airtel (step-by-step)

This project now includes direct-integration scaffolds for MTN and Airtel mobile-money collection. Below are explicit sandbox setup and test instructions so you can test end-to-end without live credentials.

Environment variables to set for sandbox testing (examples)
- FLASK_SECRET_KEY="a_random_secret"
- EMAIL_ADDRESS="zakmolan@gmail.com"
- EMAIL_PASSWORD="<your_gmail_app_password>"  # required only to send email notifications
- DONATIONS_DB="donations.db"

MTN sandbox env vars (example names used by the code)
- MTN_ENV=sandbox
- MTN_API_URL=https://sandbox.mtn.com  # replace with the actual MTN sandbox base URL they give you
- MTN_TOKEN_URL=https://sandbox.mtn.com/oauth/token  # example; use MTN docs
- MTN_CLIENT_ID=<your_mtn_sandbox_client_id>
- MTN_CLIENT_SECRET=<your_mtn_sandbox_client_secret>
- MTN_SUBSCRIPTION_KEY=<ocp-apim-subscription-key-if-required>
- MTN_WEBHOOK_SECRET=<a_shared_secret_you_configure_in_mtn_dashboard>

Airtel sandbox env vars (example names used by the code)
- AIRTEL_ENV=sandbox
- AIRTEL_API_URL=https://sandbox.airtel.com  # replace with actual Airtel sandbox URL
- AIRTEL_TOKEN_URL=https://sandbox.airtel.com/oauth/token
- AIRTEL_CLIENT_ID=<your_airtel_sandbox_client_id>
- AIRTEL_CLIENT_SECRET=<your_airtel_sandbox_client_secret>
- AIRTEL_SUBSCRIPTION_KEY=<ocp-apim-subscription-key-if-required>
- AIRTEL_WEBHOOK_SECRET=<a_shared_secret_you_configure_in_airtel_dashboard>

Notes on obtaining sandbox credentials
- MTN: Register for MTN MoMo developer sandbox. They will provide base URLs, token endpoint, client id/secret, and subscription keys. Use those exact URLs in MTN_API_URL and MTN_TOKEN_URL.
- Airtel: Register for Airtel Money sandbox/merchant access. Obtain token URL, client credentials, and subscription key.

Testing locally with ngrok
1) Install dependencies:
   pip install -r requirements.txt
2) Start the Flask app with the sandbox env vars set. Example (Linux/macOS):
   export FLASK_SECRET_KEY="test" \
          EMAIL_ADDRESS="zakmolan@gmail.com" \
          EMAIL_PASSWORD="<your_gmail_app_password>" \
          MTN_ENV="sandbox" \
          MTN_API_URL="https://<mtn-sandbox-base>" \
          MTN_TOKEN_URL="https://<mtn-token-endpoint>" \
          MTN_CLIENT_ID="..." \
          MTN_CLIENT_SECRET="..." \
          MTN_SUBSCRIPTION_KEY="..." \
          MTN_WEBHOOK_SECRET="..." \
          AIRTEL_ENV="sandbox" \
          AIRTEL_API_URL="https://<airtel-sandbox-base>" \
          AIRTEL_TOKEN_URL="https://<airtel-token-endpoint>" \
          AIRTEL_CLIENT_ID="..." \
          AIRTEL_CLIENT_SECRET="..." \
          AIRTEL_SUBSCRIPTION_KEY="..." \
          AIRTEL_WEBHOOK_SECRET="..." \
          python app.py
3) Expose your local server to the internet using ngrok so telco webhooks can reach it:
   ngrok http 5000
   Use the https URL (e.g., https://abcd1234.ngrok.io) and register the webhook endpoints in the operator dashboards as: https://abcd1234.ngrok.io/momo/webhook

Initiate a sandbox collection (example curl)
- Initiate a collection request (MTN):
  curl -X POST http://127.0.0.1:5000/momo/initiate \
    -H "Content-Type: application/json" \
    -d '{"provider":"mtn","phone":"+2567XXXXXXXX","amount":"50000","currency":"UGX","donor_email":"donor@example.com"}'
  Response includes tx_ref. The MTN sandbox should prompt or simulate the payer flow.

- Check status by calling verify:
  curl -X POST http://127.0.0.1:5000/momo/verify -H "Content-Type: application/json" -d '{"provider":"mtn","tx_ref":"<tx_ref>"}'

Simulating webhooks
- If your telco sandbox allows you to send a webhook manually, POST JSON to /momo/webhook (or use ngrok to let the operator call it when they simulate a payment). Example:
  curl -X POST https://abcd1234.ngrok.io/momo/webhook -H "Content-Type: application/json" -d '{"tx_ref":"<tx_ref>","provider":"mtn","status":"SUCCESS","phoneNumber":"+2567XXXXXXXX","amount":"50000","currency":"UGX"}'

Admin listing
- The app includes a simple admin JSON endpoint to list donations: /admin/donations?admin_key=<ADMIN_KEY>
- Set ADMIN_KEY in your env and then visit:
  curl "http://127.0.0.1:5000/admin/donations?admin_key=<ADMIN_KEY>"

What I will do next (I will now)
- Complete the sandbox-ready wiring in code (already pushed). The endpoints are in place and will call the provider endpoints when you set the MTN/Airtel sandbox env vars.
- If you want, I can help you register for MTN/Airtel developer sandbox accounts and walk through adding the keys to your Render/ngrok environment.

Tell me which step you want next:
- "Add sandbox credentials" — paste sandbox credentials here (not recommended, but I can if you want me to finish end-to-end).
- "Help register" — I will provide step-by-step guidance for registering sandbox accounts with MTN and Airtel.
- "Test with ngrok" — I will walk you through running the app locally and exposing it with ngrok to test webhooks.
