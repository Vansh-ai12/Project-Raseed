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
    Enhanced OCR pipeline for receipts (e.g., MegaMart format).
    Extracts item–price pairs and appends the final total as an item in the list.
    Uses EasyOCR + bounding box alignment for high accuracy.
    """
    try:
        # Step 1: Load image in grayscale
        image = Image.open(image_file).convert("L")
        img_np = np.array(image)
        h, w = img_np.shape[:2]

        # Step 2: Resize for better OCR accuracy
        if w < 1200:
            scale = 1200 / w
            img_np = cv2.resize(img_np, (0, 0), fx=scale, fy=scale)

        # Step 3: Enhance image for clarity
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img_np)
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Step 4: OCR using EasyOCR
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(enhanced, detail=1)

        # Step 5: Group text by Y coordinate to align rows
        lines = {}
        for (bbox, text, conf) in results:
            if conf < 0.5 or not text.strip():
                continue
            y_center = int((bbox[0][1] + bbox[2][1]) / 2)
            matched_line = None
            for key in lines.keys():
                if abs(key - y_center) < 15:
                    matched_line = key
                    break
            if matched_line is None:
                lines[y_center] = [text]
            else:
                lines[matched_line].append(text)

        # Step 6: Sort and clean lines
        sorted_lines = [lines[k] for k in sorted(lines.keys())]
        items = []
        total_amount = None  # Track total amount

        for group in sorted_lines:
            line_text = " ".join(group)
            line_text = re.sub(r"[^A-Za-z0-9₹$.,\-() ]+", " ", line_text).strip()

            # Check for total amount
            if any(x in line_text.upper() for x in ["TOTAL", "TOTAL AMOUNT", "GRAND TOTAL"]):
                total_match = re.search(r"(\d{2,6}(?:\.\d{1,2})?)$", line_text)
                if total_match:
                    try:
                        total_amount = float(total_match.group(1))
                    except:
                        pass
                continue  # Skip processing this as a normal item

            # Skip headers, metadata, taxes, discounts
            if any(x in line_text.upper() for x in [
                "CASH", "CHANGE", "TAX", "STORE", "DATE", "BILL", "AMOUNT",
                "THANK", "RECEIPT", "CARD", "PAID", "AUTH", "SHOP", "GSTIN",
                "TIME", "SECTOR", "NOIDA", "CALCULATION", "DISCOUNT", "GST"
            ]):
                continue

            # Case: "Item .... 123.45"
            match = re.search(r"([A-Za-z][A-Za-z0-9()\- ]{2,60})\s+(\d{1,5}(?:\.\d{1,2})?)$", line_text)
            if match:
                name, price = match.groups()
                try:
                    price_value = float(price)
                    items.append({"item": name.strip().title(), "price": price_value})
                except:
                    continue

        # Step 7: Add total as a final "item"
        if total_amount:
            items.append({"item": "Total Amount", "price": total_amount})

        itemsList = items

        # Step 8: Build final result
        if not items:
            return {
                "status": "partial",
                "message": "Structured data not found — returning readable OCR text",
                "raw_text": "\n".join([" ".join(g) for g in sorted_lines])
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

































