from django.shortcuts import render
from django.http import JsonResponse
from openai import OpenAI
# Create your views here.


def chatPrompt(request):
    return JsonResponse({"name": str(request)})


def chatReply(request):
    client = OpenAI(
    api_key="AIzaSyBhpwwB66OEtokZjPoikLPUjVTq5NRSnJ4",
    base_url="https://generativelanguage.googleapis.com/v1beta/"
    )


    response = client.chat.completions.create(
    model="gemini-2.5-flash",
    n=1,
    messages=[
        {"role":"system","content":"You must ONLY answer math questions. If the user asks anything else, reply exactly: 'Sorry, I can't answer that.' Do not provide any other information."}
    ,
      
        {
            "role": "user",
            "content": "Explain what are Halogens"
        }
    ]
    )

    return JsonResponse({"reply":str(response.choices[0].message.content)})