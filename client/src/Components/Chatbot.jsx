"use client";
import { useState } from "react";

export default function Chatbot({ onSend }) {
  const [userPrompt, setUserPrompt] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const handleSend = async () => {
    if (userPrompt.trim() === "" && !selectedFile) return;
    await onSend(userPrompt, selectedFile);
    setUserPrompt("");
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  const handleClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = (event) => {
      const file = event.target.files[0];
      if (file) {
        setSelectedFile(file);
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      }
    };
    input.click();
  };

  return (
    <div className="flex flex-col items-center gap-3 w-full max-w-2xl mx-auto p-4 bg-white rounded-xl shadow border border-gray-200">

      {previewUrl && (
        <div className="w-full flex justify-start mb-2">
          <div className="relative">
            <img
              src={previewUrl}
              alt="Selected"
              className="w-24 h-24 object-cover rounded-lg border border-gray-300"
            />
            <button
              onClick={() => {
                setSelectedFile(null);
                setPreviewUrl(null);
              }}
              className="absolute top-0 right-0 bg-red-500 text-white rounded-full px-2 py-1 text-xs hover:bg-red-600 hover:cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>
      )}

  
      <div className="flex items-center gap-3 w-full">
        <button
          onClick={handleClick}
          className="p-3 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 text-xl font-semibold transition hover:cursor-pointer"
        >
          +
        </button>

        <input
          type="text"
          placeholder="Ask Raseed AI..."
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          className="flex-1 bg-gray-100 focus:bg-white border border-transparent focus:border-gray-300 rounded-lg px-4 py-2 outline-none transition"
        />

        <button
          onClick={handleSend}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition hover:cursor-pointer"
        >
          Send
        </button>
      </div>
    </div>
  );
}
