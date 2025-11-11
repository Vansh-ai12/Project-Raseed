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
You are a financial advisor and bill record expert.
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
    """
    Advanced OCR pipeline for receipts
    - EasyOCR + pytesseract hybrid
    - Handles low-res and faded receipts
    - Extracts clean item-price pairs
    """
    try:
        # Step 1: Load and upscale image
        image = Image.open(image_file).convert("L")
        img_np = np.array(image)

        h, w = img_np.shape[:2]
        if w < 1200:  # Upscale small receipts
            scale = 1200 / w
            img_np = cv2.resize(img_np, (0, 0), fx=scale, fy=scale)

        # Step 2: Improve contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_np = clahe.apply(img_np)

        # Step 3: Preserve edges but smooth background
        img_np = cv2.bilateralFilter(img_np, 9, 75, 75)

        # Step 4: Sharpen + threshold for crisp letters
        img_np = cv2.adaptiveThreshold(
            img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 2
        )

        # Step 5: OCR with EasyOCR
        reader = easyocr.Reader(['en'], gpu=False)
        easy_text = "\n".join(reader.readtext(img_np, detail=0)).strip()

        # Step 6: OCR with pytesseract (fallback blend)
        tess_text = pytesseract.image_to_string(img_np, config="--oem 3 --psm 6")
        full_text = easy_text + "\n" + tess_text

        print("\n===== 🧠 HYBRID OCR OUTPUT =====")
        print(full_text)
        print("===============================\n")

        # Step 7: Clean text
        text = re.sub(r"[^A-Za-z0-9₹$.\-:\n ]+", " ", full_text)
        text = re.sub(r"[ ]{2,}", " ", text)

        # Step 8: Regex for "item + price"
        pattern = re.compile(
            r"([A-Za-z][A-Za-z0-9()\- ]{1,40})[ .:₹$-]*\s*(\d+(?:\.\d{1,2})?)"
        )

        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Skip headers and totals
            if any(x in line.upper() for x in [
                "RECEIPT", "TOTAL", "CASH", "CHANGE", "TAX",
                "STORE", "DATE", "BILL", "AMOUNT", "THANK",
                "APPROVAL", "CARD", "PAID", "AUTH", "SHOP"
            ]):
                continue

            match = pattern.search(line)
            if match:
                name, price = match.groups()
                name = name.strip().title()
                try:
                    price_value = float(price)
                    if 0.01 <= price_value <= 100000:
                        items.append({"item": name, "price": price_value})
                except ValueError:
                    continue
        itemsList = items

        # Step 9: Fallback — readable OCR text
        if not items:
            return {
                "status": "partial",
                "message": "Structured data not found — returning readable OCR text",
                "raw_text": full_text
            }

        print("✅ Extracted Items:", items)
        return {"status": "success", "items": items}

    except Exception as e:
        return {"status": "error", "message": f"OCR Pipeline Error: {str(e)}"}


@csrf_exempt
def chatPrompt(request):
    """
    Django endpoint for:
    - Performing OCR from receipt image
    - Handling normal text messages
    """
    if request.method == "POST":
        try:
            # Case 1: Image upload → OCR
            if "image" in request.FILES:
                image_file = request.FILES["image"]
                result = extract_text_from_image(image_file)
                request.session["user_prompt"] = result
                request.session.save()

                return JsonResponse({
                    "status": "success",
                    "clean_bill_text": result
                })

            # Case 2: Normal text input
            else:
                data = json.loads(request.body.decode("utf-8"))
                message = data.get("message", "")
                request.session["user_prompt"] = message
                request.session.save()

                return JsonResponse({
                    "status": "success",
                    "clean_bill_text": f"Message received: {message}"
                })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "status": "error",
        "message": "Only POST method allowed"
    }, status=405)

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
        ]
    )

    return JsonResponse({"result": response.choices[0].message.content})

