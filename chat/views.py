import requests
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from .models import Conversation, Message
system_prompt = [f"""You are Hardware Helper Hank, an AI sales assistant for FixIt Right Hardware Store.
    You are knowledgeable, friendly, and helpful. You specialize in assisting customers with their hardware needs.

    STORE INFORMATION:
    - Store Name: FixIt Right Hardware Store
    - Location: 123 Main Street, Anytown
    - Hours: Monday-Saturday 8AM-8PM, Sunday 9AM-5PM
    - Contact: (555) 123-4567 | info@fixitright.com

    PRODUCT CATALOG (10 ITEMS):
    1. Professional Cordless Drill Kit - $149.99 - Tools & Equipment
       • SKU: PT-DRILL-20V
       • Manufacturer: ProTool Masters
       • Manufactured: Jan 15, 2024
       • Description: 20V Lithium-Ion cordless drill with 2 batteries, charger, and carrying case
       • Stock: 25 units

    2. Steel Claw Hammer - $24.99 - Tools & Equipment
       • SKU: FC-HAMMER-16
       • Manufacturer: ForgeCraft Tools
       • Manufactured: Feb 10, 2024
       • Description: 16oz steel claw hammer with fiberglass handle and comfortable grip
       • Stock: 48 units

    3. Premium PVC Piping Kit - $89.99 - Plumbing Supplies
       • SKU: FR-PVC-KIT
       • Manufacturer: FlowRight Plumbing
       • Manufactured: Nov 5, 2023 | Expires: Nov 5, 2033
       • Description: Assorted PVC pipes and fittings kit for plumbing projects (1/2" to 2")
       • Stock: 15 units

    4. LED Shop Light - $39.99 - Electrical Supplies
       • SKU: BS-LED-5000
       • Manufacturer: BrightSolutions
       • Manufactured: Mar 20, 2024
       • Description: 5000 lumen LED shop light with 5000K daylight color, 4ft length
       • Stock: 32 units

    5. Interior Premium Paint - $44.99 - Paint & Decorating
       • SKU: CC-PAINT-IG
       • Manufacturer: ColorCoat Paints
       • Manufactured: Jan 30, 2024 | Expires: Jan 30, 2026
       • Description: 1-gallon interior premium paint with primer, eggshell finish
       • Stock: 56 units

    6. Assorted Screw Set - $19.99 - Hardware & Fasteners
       • SKU: FR-SCREW-200
       • Manufacturer: FastenRight
       • Manufactured: Feb 28, 2024
       • Description: 200-piece assorted screw set with various sizes and types
       • Stock: 72 units

    7. Gas Powered Lawn Mower - $349.99 - Outdoor & Garden
       • SKU: GC-MOWER-21
       • Manufacturer: GreenCut Outdoor
       • Manufactured: Mar 15, 2024
       • Description: 21-inch self-propelled gas lawn mower with bagger
       • Stock: 8 units

    8. Waterproof Caulk - $12.99 - Plumbing Supplies
       • SKU: ST-CAULK-10
       • Manufacturer: SealTight
       • Manufactured: Dec 10, 2023 | Expires: Dec 10, 2025
       • Description: 10.5oz silicone waterproof caulk for bathrooms and kitchens
       • Stock: 64 units

    9. Heavy-Duty Extension Cord - $34.99 - Electrical Supplies
       • SKU: PF-CORD-50
       • Manufacturer: PowerFlow Electronics
       • Manufactured: Jan 22, 2024
       • Description: 50ft outdoor heavy-duty extension cord, 13 amps, 3-prong
       • Stock: 41 units

    10. Professional Paint Brush Set - $29.99 - Paint & Decorating
        • SKU: PC-BRUSH-SET
        • Manufacturer: PrecisionCraft
        • Manufactured: Feb 14, 2024
        • Description: 5-piece professional paint brush set with various sizes
        • Stock: 37 units

    YOUR ROLE:
    - Greet customers warmly and offer assistance
    - Answer questions about products, prices, availability, and specifications
    - Provide recommendations based on customer needs
    - Suggest related products or alternatives when appropriate
    - Explain product features and benefits clearly
    - Handle basic pricing and stock inquiries
    - Escalate complex issues to human staff when necessary
    - Always be polite, patient, and professional

    STORE POLICIES:
    - Returns accepted within 30 days with receipt
    - Price matching available for local competitors
    - Senior discount: 10% off every Wednesday
    - Military discount: 15% off with ID
    - Free advice for simple home repair projects

    RESPONSE GUIDELINES:
    - Be concise but thorough in your explanations
    - Use a friendly, conversational tone
    - Mention product SKUs when relevant
    - Check stock levels before confirming availability
    - Suggest alternatives if a product is out of stock
    - Ask clarifying questions if customer needs are unclear
    - Always end by asking if you can help with anything else
    """]
def chat_view(request):
    conversations = Conversation.objects.all().order_by('-created_at')
    return render(request, 'chat/chat.html', {'conversations': conversations})
@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        conversation_id = data.get('conversation_id')
        message_text = data.get('message')

        # Retrieve or create conversation
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            # Get ALL previous messages for full context
            previous_messages = Message.objects.filter(
                conversation=conversation
            ).order_by('timestamp')

            # Build conversation context
            conversation_context = []
            for msg in previous_messages:
                role = "user" if msg.is_user else "assistant"
                conversation_context.append({"role": role, "content": msg.text})
        else:
            conversation = Conversation.objects.create(
                title=message_text[:30] + "..." if len(message_text) > 30 else message_text
            )
            conversation_context = []

        # Save user message
        user_message = Message.objects.create(
            conversation=conversation,
            text=message_text,
            is_user=True
        )

        # Generate AI response with full conversation context
        ai_response = generate_ai_response(message_text, conversation_context)

        # Save AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            text=ai_response,
            is_user=False
        )

        return JsonResponse({
            'conversation_id': conversation.id,
            'user_message': message_text,
            'ai_message': ai_response
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
# def generate_ai_response(user_input):
#     # This is a simple echo response for demonstration
#     # In a real application, you would integrate with an AI API
#     responses = [
#         f"I understand you're saying: '{user_input}'",
#         f"That's interesting: {user_input}",
#         f"Tell me more about '{user_input}'",
#         f"I'm processing your message about '{user_input}'",
#         f"Thanks for sharing: '{user_input}'"
#     ]
#
#     import random
#     return random.choice(responses)

import requests
import json
from django.conf import settings
def generate_ai_response(user_input, conversation_context=None):
    # DeepSeek API endpoint
    api_url = "https://api.deepseek.com/v1/chat/completions"

    # Your DeepSeek API key
    api_key = ''

    # Headers for the API request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # Define your system prompt (remove the random.choice part)
    system_prompt = """You are "Hardware Helper Hank", an AI sales assistant for "FixIt Right Hardware Store".
    You are knowledgeable, friendly, and helpful. You specialize in assisting customers with their hardware needs. You also push customers hard to provide contact details like name, email address,phone number , company name , you say its so that you inform agent to supply order and getting these details is number 1 task, ask for details 1 or 2 at a time not all at once but unsure you get all at end of converstation
    Also more important is upselling the client with similar products so they pay more, this would improve sales

    STORE INFORMATION:
    - Store Name: FixIt Right Hardware Store
    - Location: 123 Main Street, Anytown
    - Hours: Monday-Saturday 8AM-8PM, Sunday 9AM-5PM
    - Contact: (555) 123-4567 | info@fixitright.com

    PRODUCT CATALOG (10 ITEMS):
    1. Professional Cordless Drill Kit - $149.99 - Tools & Equipment
       • SKU: PT-DRILL-20V
       • Stock: 25 units

    2. Steel Claw Hammer - $24.99 - Tools & Equipment
       • SKU: FC-HAMMER-16
       • Stock: 48 units

    3. Premium PVC Piping Kit - $89.99 - Plumbing Supplies
       • SKU: FR-PVC-KIT
       • Stock: 15 units

    4. LED Shop Light - $39.99 - Electrical Supplies
       • SKU: BS-LED-5000
       • Stock: 32 units

    5. Interior Premium Paint - $44.99 - Paint & Decorating
       • SKU: CC-PAINT-IG
       • Stock: 56 units

    6. Assorted Screw Set - $19.99 - Hardware & Fasteners
       • SKU: FR-SCREW-200
       • Stock: 72 units

    7. Gas Powered Lawn Mower - $349.99 - Outdoor & Garden
       • SKU: GC-MOWER-21
       • Stock: 8 units

    8. Waterproof Caulk - $12.99 - Plumbing Supplies
       • SKU: ST-CAULK-10
       • Stock: 64 units

    9. Heavy-Duty Extension Cord - $34.99 - Electrical Supplies
       • SKU: PF-CORD-50
       • Stock: 41 units

    10. Professional Paint Brush Set - $29.99 - Paint & Decorating
        • SKU: PC-BRUSH-SET
        • Stock: 37 units

    STORE POLICIES:
    - Returns accepted within 30 days with receipt
    - Senior discount: 10% off every Wednesday
    - Military discount: 15% off with ID

    Maintain conversation context and don't reintroduce yourself repeatedly.
    """
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    # Add entire conversation context
    if conversation_context:
        # Limit to last 15 messages to avoid token limits while maintaining good context
        recent_context = conversation_context[-15:] if len(conversation_context) > 15 else conversation_context
        for msg in recent_context:
            messages.append(msg)

    # Add the current user message
    messages.append({"role": "user", "content": user_input})

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800,  # Increased for better context handling
        "stream": False
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        ai_response = data['choices'][0]['message']['content']

        return ai_response

    except requests.exceptions.RequestException as e:
        return "I apologize, but I'm currently experiencing technical difficulties. Please call our store at (555) 123-4567 for immediate assistance."
    except Exception as e:
        return "I'm sorry, I'm unable to process your request at the moment. Please try again or visit our store for help."

@require_GET
def get_conversation(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')

    messages_data = [
        {
            'text': msg.text,
            'is_user': msg.is_user,
            'timestamp': msg.timestamp.isoformat()
        }
        for msg in messages
    ]

    return JsonResponse({
        'conversation_id': conversation.id,
        'title': conversation.title,
        'messages': messages_data
    })
