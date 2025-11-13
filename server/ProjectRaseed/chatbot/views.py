import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
import re
import io
from PIL import Image
import numpy as np
from dotenv import load_dotenv
import os
import cv2
import easyocr
import pytesseract



SYSTEM_PROMPT = """
You are a financial advisor and bill record expert , Also Your name is RASEED AI.
if anyone asks -> what is your name? You should reply it saying I am Raseed AI how can I help you?
Your goal is to give **direct, specific, and helpful answers** related to money management,
spending, savings, and investments.

Rules:
1. Always answer finance-related questions with clear reasoning and step-by-step advice.
2. If the user asks about anything unrelated to finance, strictly reply with: "Sorry, I can't answer that."
3. Never introduce yourself or say hello; respond directly with advice.
4. Keep your tone expert, concise, and professional.
"""

itemsList = []



def extract_text_from_image(image_file):
    global itemsList

    try:
        # Step 1: Load grayscale image
        image = Image.open(image_file).convert("L")
        img_np = np.array(image)

        # Resize for clarity
        h, w = img_np.shape[:2]
        if w < 1200:
            scale = 1200 / w
            img_np = cv2.resize(img_np, (0, 0), fx=scale, fy=scale)

        # Enhance
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img_np)
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # OCR
        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(enhanced, detail=1)

        # Group lines
        lines = {}
        for (bbox, text, conf) in results:
            if conf < 0.5 or not text.strip():
                continue
            y_center = int((bbox[0][1] + bbox[2][1]) / 2)
            matched_line = None
            for key in lines:
                if abs(key - y_center) < 15:
                    matched_line = key
                    break
            if matched_line is None:
                lines[y_center] = [text]
            else:
                lines[matched_line].append(text)

        sorted_lines = [lines[k] for k in sorted(lines)]

        items = []
        total_amount = None

        for group in sorted_lines:
            line_text = " ".join(group)
            clean = re.sub(r"[^A-Za-z0-9₹$.,\-()% ]+", " ", line_text).strip()

            # Extract TOTAL
            if "TOTAL" in clean.upper():
                match = re.search(r"(\-?\d{1,6}(?:\.\d{1,2})?)$", clean)
                if match:
                    items.append({
                        "item": "Total Amount",
                        "price": float(match.group(1))
                    })
                continue

            # Extract Calculation / Subtotal
            if "CALCULATION" in clean.upper():
                match = re.search(r"(\-?\d{1,6}(?:\.\d{1,2})?)$", clean)
                if match:
                    items.append({
                        "item": "Calculation",
                        "price": float(match.group(1))
                    })
                continue

            # Extract GST
            if "GST" in clean.upper():
                match = re.search(r"(\-?\d{1,6}(?:\.\d{1,2})?)$", clean)
                if match:
                    gst_val = float(match.group(1))
                    items.append({
                        "item": clean.split()[0] + " (GST)",
                        "price": gst_val
                    })
                continue

            # Extract Discount
            if "DISCOUNT" in clean.upper():
                match = re.search(r"(\-?\d{1,6}(?:\.\d{1,2})?)$", clean)
                if match:
                    items.append({
                        "item": "Discount Applied",
                        "price": float(match.group(1))
                    })
                continue

            # Regular item extraction
            match = re.search(r"([A-Za-z][A-Za-z0-9()\- ]{2,60})\s+(\-?\d{1,6}(?:\.\d{1,2})?)$", clean)
            if match:
                name, price = match.groups()
                items.append({
                    "item": name.strip().title(),
                    "price": float(price)
                })

        itemsList = items
        return {"status": "success", "items": items}

    except Exception as e:
        return {"status": "error", "message": f"OCR Pipeline Error: {str(e)}"}



@csrf_exempt
def chatPrompt(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Only POST method allowed"}, status=405)

    try:

        if request.content_type.startswith("multipart/"):
            if "image" in request.FILES:
                image_file = request.FILES["image"]
                result = extract_text_from_image(image_file)
                result_text = json.dumps(result,default = str)

                message = request.POST.get("message", "")

                final_result = "This is the bill consider this " + result_text + " " + message

                request.session["user_prompt"] = final_result
                


                request.session.save()

                return JsonResponse({
                    "status": "success",
                    "clean_bill_text": final_result
                })


            message = request.POST.get("message", "")
            request.session["user_prompt"] = message
            request.session.save()

            return JsonResponse({"status": "success", "clean_bill_text": message})

        else:
            body = json.loads(request.body.decode("utf-8"))
            message = body.get("message", "")

            request.session["user_prompt"] = message
            
            request.session.save()

            return JsonResponse({"status": "success", "clean_bill_text": message})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


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
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
    )

    return JsonResponse({"result":response.choices[0].message.content })


def statusInfo(request):
    return JsonResponse({
    "status": "success",
    "items": itemsList
}, safe=False)



































