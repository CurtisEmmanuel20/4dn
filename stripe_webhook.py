import os
import sqlite3
import stripe
from flask import request, jsonify
from app import app

# Set your Stripe webhook secret as an environment variable
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle successful payment for the Lifetime Pass
    if event['type'] == 'checkout.session.completed':
        session_obj = event['data']['object']
        customer_email = session_obj.get('customer_details', {}).get('email')
        if customer_email:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('UPDATE users SET season_pass = 1 WHERE email = ?', (customer_email,))
            conn.commit()
            conn.close()
    return jsonify({'status': 'success'})
