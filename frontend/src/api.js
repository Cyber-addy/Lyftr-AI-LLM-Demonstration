const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";


export async function sendMessage({
  sessionId,
  message,
  systemPrompt,
}) {
  const body = {
    session_id: sessionId,
    message: message,
  };

  if (systemPrompt.trim()) {
    body.system_prompt = systemPrompt.trim();
  }

  const response = await fetch(
    `${API_URL}/chat`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(body),
    }
  );

  let data = {};

  try {
    data = await response.json();
  } catch {
    // Keep empty object
  }

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "Unable to get an AI response."
    );
  }

  return data;
}


export async function checkHealth() {
  const response = await fetch(
    `${API_URL}/health`
  );

  if (!response.ok) {
    throw new Error(
      "Backend unavailable"
    );
  }

  return response.json();
}