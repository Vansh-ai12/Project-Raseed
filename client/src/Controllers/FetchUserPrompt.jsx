export default async function FetchUserPrompt(prompt) {
  // Step 1 — Send the message to /chatbot/prompt/
  await fetch("http://127.0.0.1:8000/chatbot/prompt/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ "message": prompt }),
    credentials: "include", // <── VERY IMPORTANT
  });

  // Step 2 — Get the reply from /chatbot/reply/
  const res = await fetch("http://127.0.0.1:8000/chatbot/reply/", {
    method: "POST",
    credentials: "include", // <── MUST match session
  });
  const data = await res.json();
  console.log(data);
}
