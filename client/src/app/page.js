import Logo from "@/Components/Logo";
import Chatbot from "@/Components/Chatbot";
import Status from "@/Components/Status";
export default function HomePage() {
  return (
    <div class="flex-col">
      <div class="flex justify-between">
        <Logo />
        <Status/>
      </div>
      <div className="w-full max-w-5xl mx-auto h-[60vh] bg-white border border-gray-200 rounded-2xl shadow-inner overflow-y-auto p-6 scrollbar-hide mt-5">

        <div className="text-gray-700 leading-relaxed">
          <p>
            Hello 👋, I’m{" "}
            <span className="font-semibold text-blue-500">Raseed AI</span>. Ask
            me anything, and I’ll do my best to help!
          </p>
        </div>
      </div>

      <div class="flex mt-10 justify-center">
        <Chatbot />
      </div>
    </div>
  );
}
