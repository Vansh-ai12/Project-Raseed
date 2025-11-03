"use client";

export default function Chatbot() {
  return (
    <div className="w-full max-w-2xl mx-auto p-4 flex items-center gap-3 bg-white rounded-xl shadow border border-gray-200 border-r-8">
      <button className="p-3 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 text-xl font-semibold transition hover:cursor-pointer">
        +
      </button>

      <input
        type="text"
        placeholder="Ask Raseed AI..."
        className="flex-1 bg-gray-100 focus:bg-white border border-transparent focus:border-gray-300 rounded-lg px-4 py-2 outline-none transition"
      />
      <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition hover:cursor-pointer">
        Send
      </button>
    </div>
  );
}
