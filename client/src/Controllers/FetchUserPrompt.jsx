export default async function FetchUserPrompt(prompt, selectedFile = null) {
  try {
    let response;

   
    if (selectedFile) {
      const formData = new FormData();
      formData.append("image", selectedFile);
      formData.append("message", prompt || "");

      response = await fetch("http://127.0.0.1:8000/chatbot/prompt/", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
    } else {
      response = await fetch("http://127.0.0.1:8000/chatbot/prompt/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: prompt }),
        credentials: "include",
      });
    }

    const promptData = await response.json();
    console.log("✅ Prompt Response:", promptData);

    // Step 2️⃣ — Ask Gemini for reply (via /chatbot/reply/)
    const replyResponse = await fetch("http://127.0.0.1:8000/chatbot/reply/", {
      method: "POST",
      credentials: "include", // must include for session access
    });

    const replyData = await replyResponse.json();
    console.log("💬 Gemini Reply:", replyData);


    return {
      clean_bill_text: replyData.result || promptData.clean_bill_text,
    };
  } catch (err) {
    console.error("❌ FetchUserPrompt Error:", err);
    return { error: "Failed to connect to server." };
  }
}
