"use client";
import Logo from "@/Components/Logo";
import Chatbot from "@/Components/Chatbot";
import Status from "@/Components/Status";
import FetchUserPrompt from "@/Controllers/FetchUserPrompt";
import { useState } from "react";

export default function HomePage() {
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);

  // 🧠 Handle send from Chatbot
  const handleUserSend = async (prompt, file) => {
    if (!prompt.trim() && !file) return;

    // 1️⃣ Instantly show user's message
    const newMsg = {
      sender: "user",
      text: prompt,
      image: file ? URL.createObjectURL(file) : null,
    };
    setConversation((prev) => [...prev, newMsg]);
    setLoading(true);

    try {
      // 2️⃣ Call backend (sending both text + image)
      const res = await FetchUserPrompt(prompt, file);

      // 3️⃣ Create bot message
      let rawText =
        typeof res.clean_bill_text === "string"
          ? res.clean_bill_text
          : JSON.stringify(res.clean_bill_text, null, 2);

      // Remove markdown formatting (*, _, #, `, >, etc.)
      const cleanText = rawText
        .replace(/[*_`#>-]+/g, "")
        .replace(/\n{2,}/g, "\n") // compress extra newlines
        .trim();

      const botMsg = { sender: "bot", text: cleanText };
      setConversation((prev) => [...prev, botMsg]);
    } catch (err) {
      setConversation((prev) => [
        ...prev,
        { sender: "bot", text: "❌ Server error. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-col">
      {/* Header */}
      <div className="flex justify-between">
        <Logo />
        <Status />
      </div>

      {/* 💬 Chat Window */}
      <div className="w-full max-w-5xl mx-auto h-[60vh] bg-white border border-gray-200 rounded-2xl shadow-inner overflow-y-auto p-6 scrollbar-hide mt-5">
        <div className="text-gray-700 leading-relaxed space-y-4">
          {/* 🧠 Default Greeting */}
          {conversation.length === 0 && (
            <p>
              Hello 👋, I’m{" "}
              <span className="font-semibold text-blue-500">Raseed AI</span>.
              Upload your bill or ask me a question!
            </p>
          )}

          {/* 💬 Messages */}
          {conversation.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-xl shadow-sm transition-all ${
                  msg.sender === "user"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                {msg.image && (
                  <img
                    src={msg.image}
                    alt="uploaded"
                    className="w-32 h-32 object-cover rounded-md mb-2 border border-gray-300"
                  />
                )}
                <pre className="whitespace-pre-wrap">{msg.text}</pre>
              </div>
            </div>
          ))}

          {/* 🌀 ChatGPT-style Loading Bubble */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-700 px-4 py-3 rounded-xl inline-flex items-center space-x-2 shadow-sm">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ✉️ Input Area */}
      <div className="flex mt-10 justify-center">
        <Chatbot onSend={handleUserSend} />
      </div>
    </div>
  );
}
