import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
import requests
import re
from pytesseract import image_to_string
from PIL import Image
import io


SYSTEM_PROMPT = """
You are a financial advisor and bill record expert.
Your goal is to give **direct, specific, and helpful answers** related to money management,
spending, savings, and investments.

Rules:
1. Always answer finance-related questions with clear reasoning and step-by-step advice.
2. If the user asks about anything unrelated to finance, strictly reply with: "Sorry, I can't answer that."
3. Never introduce yourself or say hello; respond directly with advice.
4. Keep your tone expert, concise, and professional.

Examples:

Q: How to invest 5 lacs?
A: You can invest ₹5,00,000 by diversifying:
- 40% (₹2,00,000) into index mutual funds (like Nifty 50)
- 30% (₹1,50,000) into fixed deposits or short-term debt funds
- 20% (₹1,00,000) into gold ETFs
- 10% (₹50,000) as emergency cash in savings.

Q: What is (a+b)²?
A: Sorry, I can't answer that.
"""


def is_relevant_line(line):
    line = line.strip()
    if not line:
        return False

    clean_line = re.sub(r'[^\w\s\.]', '', line)
    numbers = re.findall(r'\d+\.\d+|\d+', clean_line)

    #  Keep if decimal numbers (money-like)
    for num in numbers:
        if '.' in num:
            return True

    #  Keep if item pattern like "1x"
    if re.search(r'\b\d+x\b', clean_line, re.IGNORECASE):
        return True

    # Keep if money-related keywords
    if re.search(r'\b(CASH|CHANGE|TOTAL)\b', clean_line, re.IGNORECASE):
        return True

    return False


@csrf_exempt
def chatPrompt(request):
    if request.method == "POST":
        final_text = ""

        if "image" in request.FILES:
            image_file = request.FILES["image"]
            img = Image.open(io.BytesIO(image_file.read()))
            raw_text = image_to_string(img)

            filtered_lines = [
                re.sub(r'\s+', ' ', re.sub(r'[^\w\s\.]', '', line.strip()))
                for line in raw_text.splitlines()
                if is_relevant_line(line)
            ]
            final_text = "\n".join(filtered_lines)
            request.session["ocr_text"] = final_text
            request.session.save()

        else:
            data = json.loads(request.body.decode('utf-8'))
            message = data.get("message", "")
            request.session["user_prompt"] = message  # <── Store safely
            request.session.save()
            print("SESSION KEY PROMPT:", request.session.session_key)
        return JsonResponse({
            "status": "success",
            "clean_bill_text": final_text
        })

    return JsonResponse({"error": "Only POST method allowed"}, status=405)


@csrf_exempt
def chatReply(request):

    client = OpenAI(
        api_key="AIzaSyAyIt0fQ1gZV-r_HTCPwt42pf7l2QyiSKI",
        base_url="https://generativelanguage.googleapis.com/v1beta/"
    )
    print("SESSION KEY REPLY:", request.session.session_key)
    user_prompt = request.session.get("user_prompt", "")
    if not user_prompt:
        return JsonResponse({"error": "No user message found"}, status=400)

    response = client.chat.completions.create(
        model="gemini-2.5-flash",  # safer model for testing
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    return JsonResponse({"result": response.choices[0].message.content})



