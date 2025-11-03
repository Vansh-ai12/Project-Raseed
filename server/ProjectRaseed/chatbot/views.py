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
You are transcations and bill record expert like an Accountant, You keep the track of payments and suggest better
way to spend some amount of money. Also whenever asks any questions unrelated to finance just say I am sorry.

Example:1 
Q: What is (a+b) whole sqaure?
A: Sorry, I can't answer that.

Q: What is Inertia?
A:Sorry , I cant answer that.

Q.As you saw my bill where should I spend my leftamount?
A. Buy a course or some books related to investments or you can reinvest.

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
        if "image" in request.FILES:
            # Run OCR if image uploaded
            image_file = request.FILES["image"]
            img = Image.open(io.BytesIO(image_file.read()))
            raw_text = image_to_string(img)

            # Clean text
            filtered_lines = []
            for line in raw_text.splitlines():
                if is_relevant_line(line):
                    line_clean = re.sub(r'[^\w\s\.]', '', line).strip()
                    line_clean = re.sub(r'\s+', ' ', line_clean)
                    filtered_lines.append(line_clean)

            final_text = "\n".join(filtered_lines)
        else:
            # If no image, just save empty text
            final_text = "No bill data provided."

        # Save in session for chatReply
        request.session["ocr_text"] = final_text

        return JsonResponse({
            "status": "success",
            "clean_bill_text": final_text
        })

    return JsonResponse({"error": "Only POST method allowed"}, status=405)



@csrf_exempt
def chatReply(request):
    USER_PROMPT = "How to spend 500 rs?"

    client = OpenAI(
        api_key="AIzaSyAyIt0fQ1gZV-r_HTCPwt42pf7l2QyiSKI",
        base_url="https://generativelanguage.googleapis.com/v1beta/"
    )

    response = client.chat.completions.create(
        model="gemini-2.5-flash",  # safer model for testing
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ]
    )

    return JsonResponse({"result": response.choices[0].message.content})