from flask import Blueprint, request, jsonify, session
from aquasense.db_helper import fetch_one, fetch_all
from aquasense.utils.decorators import login_required
import anthropic
import json

chatbot_bp = Blueprint('chatbot', __name__)

def get_user_context(user_id):
    """Fetch user's data to give the chatbot context"""

    # Get user details
    user = fetch_one(
        """SELECT name, threshold, streak, conservation_score,
         tariff_rate, city FROM users WHERE id = ?""",
        (user_id,)
    )

    # Get today's usage
    today_usage = fetch_one(
        """SELECT amount_litres FROM usage_records
         WHERE user_id = ?
         ORDER BY date DESC LIMIT 1""",
        (user_id,)
    )

    # Get weekly total
    weekly = fetch_one(
        """SELECT ROUND(SUM(amount_litres), 2) as total
         FROM usage_records
         WHERE user_id = ?
         AND date >= date('now', '-7 days')""",
        (user_id,)
    )

    # Get monthly total
    monthly = fetch_one(
        """SELECT ROUND(SUM(amount_litres), 2) as total
         FROM usage_records
         WHERE user_id = ?
         AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')""",
        (user_id,)
    )

    # Get average daily usage
    avg = fetch_one(
        """SELECT ROUND(AVG(amount_litres), 2) as avg
         FROM usage_records WHERE user_id = ?""",
        (user_id,)
    )

    # Get recent alerts
    alerts = fetch_all(
        """SELECT message FROM alerts
         WHERE user_id = ?
         ORDER BY triggered_at DESC LIMIT 3""",
        (user_id,)
    )

    # Get badges
    badges = fetch_all(
        """SELECT badge_name FROM badges WHERE user_id = ?""",
        (user_id,)
    )

    # Get recent anomalies
    anomalies = fetch_all(
        """SELECT date, amount_litres FROM usage_records
         WHERE user_id = ? AND is_anomaly = 1
         ORDER BY date DESC LIMIT 3""",
        (user_id,)
    )

    # Get latest prediction
    prediction = fetch_all(
        """SELECT predicted_date, predicted_litres
         FROM predictions
         WHERE user_id = ?
         ORDER BY predicted_date ASC LIMIT 7""",
        (user_id,)
    )

    # Build context string
    context = f"""
    User Profile:
    - Name: {user['name']}
    - City: {user['city']}
    - Daily Threshold: {user['threshold']} litres
    - Water Tariff Rate: ₹{user['tariff_rate']} per litre
    - Current Streak: {user['streak']} days under threshold
    - Conservation Score: {user['conservation_score']}%

    Usage Data:
    - Most Recent Usage: {today_usage['amount_litres'] if today_usage else 'No data yet'} litres
    - This Week Total: {weekly['total'] if weekly['total'] else 0} litres
    - This Month Total: {monthly['total'] if monthly['total'] else 0} litres
    - Average Daily Usage: {avg['avg'] if avg['avg'] else 0} litres

    Badges Earned: {', '.join([b['badge_name'] for b in badges]) if badges else 'No badges yet'}

    Recent Alerts: {', '.join([a['message'] for a in alerts]) if alerts else 'No active alerts'}

    Recent Anomalies: {', '.join([f"{a['date']} ({a['amount_litres']}L)" for a in anomalies]) if anomalies else 'None detected'}

    7-Day Predictions: {', '.join([f"{p['predicted_date']}: {p['predicted_litres']}L" for p in prediction]) if prediction else 'No predictions yet'}
    """

    return context


@chatbot_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    user_id = session['user_id']
    user_message = request.json.get('message', '').strip()
    chat_history = request.json.get('history', [])
    
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400
    
    # Get user's data as context
    context = get_user_context(user_id)
    
    # Build message history for multi-turn conversation
    messages = []
    for msg in chat_history[-6:]:  # Keep last 6 messages for context
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Call Claude API
    client = anthropic.Anthropic()
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=f"""You are AquaBot, a friendly and helpful water conservation 
        assistant for the AquaSense platform. You help users understand their 
        water usage patterns, interpret their data, and provide personalized 
        conservation tips.

        Here is the current user's real data:
        {context}

        Guidelines:
        - Always refer to the user by their first name
        - Give specific, data-driven answers using their actual numbers
        - Be encouraging and positive about conservation efforts
        - Keep responses concise and friendly — 2 to 4 sentences max
        - If asked about something unrelated to water usage, 
          politely redirect to water conservation topics
        - Use simple language, avoid technical jargon
        - When mentioning costs, always use ₹ symbol
        - If the user has no data yet, encourage them to start logging
        """,
        messages=messages
    )
    
    bot_reply = response.content[0].text
    
    return jsonify({'reply': bot_reply})