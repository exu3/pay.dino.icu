import os
import json
import stripe

from flask import Flask, render_template, redirect, request

from replit import web, db

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
base_url = "".join([
  "https://",
  os.environ["REPL_SLUG"],
  ".",
  os.environ["REPL_OWNER"],
  ".repl.co"
])

app = Flask(__name__)

users = web.UserStore()

@app.route("/")
def index():
  return render_template("index.html")

@app.route("/secret")
@web.authenticated
def secret():
  if users.current.get("subscription_status", "") == "active":
    return render_template("secret.html")
  else:
    return redirect("/paywall")

@app.route("/paywall")
@web.authenticated
def paywall():
  return render_template("paywall.html")

@app.route("/checkout", methods=["POST"])
@web.authenticated
def checkout():
  # create a checkout session
  session = stripe.checkout.Session.create(
    success_url=base_url + "/secret?id={CHECKOUT_SESION_ID}",
    cancel_url=base_url,
    line_items=[
      {
        "price": "price_1JxpV5A3oBOH0qmM3ws9DmJP",
        "quantity": 1,
      },
    ],
    metadata={
      'username': users.current.username,
    },
    subscription_data={
      'metadata': {
        'username': users.current.username,
      }
    },
    mode="subscription",
  )
  # redirect to checkout
  return redirect(session.url, code=303)

@app.route("/webhook", methods=["POST"])
def webhook():
  payload = request.data
  event = None

  try:
    event = stripe.Event.construct_from(
      json.loads(payload), stripe.api_key
    )
  except ValueError:
    # Invalid payload
    return "Invalid payload"

  # Handle the event
  if event.type == 'checkout.session.completed':
    session = event.data.object
    # lookup the users
    username = session.metadata['username']
    user = users[username]
    user['subscription_status'] = 'active'
    # set their subscriptions status to "active"
  elif event.type == 'customer.subscription.deleted':
    subscription = event.data.object
    username = subscription.metadata['username']
    user = users[username]
    user['subscription_status'] = 'cancelled'
  else:
    print('Unhandled event type {}'.format(event.type))

  return ""

# manually set my subscription status to not active for testing
# users["eilla"]["subscription_status"] = ""

web.run(app)