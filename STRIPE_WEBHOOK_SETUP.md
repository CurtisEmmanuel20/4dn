# Stripe Webhook Setup Instructions

1. Go to your Stripe Dashboard → Developers → Webhooks.
2. Click "Add endpoint" and enter your endpoint URL (e.g., https://yourdomain.com/stripe-webhook or http://localhost:5000/stripe-webhook for local testing).
3. Select "Listen to events on your account" and add the event type: `checkout.session.completed`.
4. After creating the webhook, copy the "Signing secret" and add it to your `.env` file as:
   STRIPE_WEBHOOK_SECRET=whsec_...
5. Restart your Flask app after editing `.env`.

# Testing Locally
- Use the Stripe CLI to forward webhook events to your local server:
  stripe listen --forward-to localhost:5000/stripe-webhook
- The CLI will print a webhook secret; use that in your `.env` for local testing.

# Security
- Never commit your `.env` file or any secret keys to git.
- Your `.gitignore` is already set up to protect secrets.

# Troubleshooting
- Check your Flask logs for webhook delivery errors.
- Ensure your server is reachable from Stripe (use ngrok or Stripe CLI for local dev).

# Next Steps
- Your backend and webhook logic are ready for Stripe Checkout and automatic user access updates!
