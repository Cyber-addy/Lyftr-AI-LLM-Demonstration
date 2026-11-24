import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  checkHealth,
  sendMessage,
} from "./api";

import "./App.css";


function App() {

  // New session every page load
  const [sessionId] = useState(
    () => `s-${crypto.randomUUID()}`
  );

  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [systemPrompt, setSystemPrompt] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [backendOnline, setBackendOnline] =
    useState(false);

  const bottomRef = useRef(null);


  // Check backend
  useEffect(() => {

    checkHealth()
      .then(() => {
        setBackendOnline(true);
      })
      .catch(() => {
        setBackendOnline(false);
      });

  }, []);


  // Auto scroll
  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });

  }, [messages, loading]);


  async function handleSend() {

    const cleanMessage = input.trim();

    if (
      !cleanMessage ||
      loading
    ) {
      return;
    }


    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: cleanMessage,
    };


    setMessages((current) => [
      ...current,
      userMessage,
    ]);


    // Assignment requires empty input
    // after sending.
    setInput("");

    setLoading(true);


    try {

      const data = await sendMessage({
        sessionId,
        message: cleanMessage,
        systemPrompt,
      });


      const assistantMessage = {

        id: crypto.randomUUID(),

        role: "assistant",

        content: data.reply,

        metadata: data.metadata,

      };


      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);


      setBackendOnline(true);

    } catch (error) {

      const errorMessage = {

        id: crypto.randomUUID(),

        role: "error",

        content:
          error.message ||
          "Unable to get a response.",

      };


      setMessages((current) => [
        ...current,
        errorMessage,
      ]);

    } finally {

      setLoading(false);

    }
  }


  function handleKeyDown(event) {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      handleSend();

    }
  }


  return (

    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div className="brand">

          <div className="logo">
            ✦
          </div>

          <div>

            <h1>
              Lyftr AI
            </h1>

            <p>
              Resilient AI Assistant
            </p>

          </div>

        </div>


        <div
          className={
            backendOnline
              ? "status online"
              : "status offline"
          }
        >

          <span className="status-dot" />

          {backendOnline
            ? "API Online"
            : "API Offline"}

        </div>

      </header>


      {/* MAIN */}

      <main className="main">


        {/* SYSTEM PROMPT */}

        <section className="system-section">

          <label htmlFor="systemPrompt">

            System prompt

            <span>
              {" "}Optional
            </span>

          </label>


          <input

            id="systemPrompt"

            data-testid="system-prompt-input"

            value={systemPrompt}

            onChange={(event) =>
              setSystemPrompt(
                event.target.value
              )
            }

            placeholder=
              "You are a helpful AI assistant."

          />

        </section>


        {/* WELCOME */}

        {messages.length === 0 && (

          <section className="welcome">

            <div className="welcome-icon">
              ✦
            </div>

            <h2>
              How can I help you?
            </h2>

            <p>
              Ask anything and continue
              the conversation naturally.
            </p>

          </section>

        )}


        {/* CHAT */}

        <section className="messages">


          {messages.map((message) => (

            <div
              key={message.id}

              className={
                `message-row ${message.role}`
              }
            >


              {/* USER */}

              {message.role === "user" && (

                <div className="user-message">

                  <div className="message-label">
                    You
                  </div>

                  <div className="bubble user-bubble">

                    {message.content}

                  </div>

                </div>

              )}


              {/* ASSISTANT */}

              {message.role ===
                "assistant" && (

                <div

                  className="assistant-message"

                  data-testid=
                    "assistant-message"

                >

                  <div className="message-label">

                    ✦ Lyftr AI

                  </div>


                  <div className=
                    "bubble assistant-bubble"
                  >


                    <div className="reply-text">

                      {message.content}

                    </div>


                    {/* METADATA */}

                    <div className="metadata">


                      <span

                        className={
                          message.metadata
                            ?.resolution_source ===
                          "LLM_CACHE"

                            ? "meta-chip cache"

                            : "meta-chip live"
                        }

                        data-testid="meta-source"

                      >

                        {
                          message.metadata
                            ?.resolution_source
                        }

                      </span>


                      <span
                        className="meta-chip"
                        data-testid="meta-model"
                      >

                        {
                          message.metadata
                            ?.model
                        }

                      </span>


                      <span
                        className="meta-chip"
                        data-testid="meta-latency"
                      >

                        {
                          message.metadata
                            ?.latency_ms
                        }{" "}
                        ms

                      </span>


                      <span className="meta-chip">

                        Input:{" "}

                        <span
                          data-testid=
                            "meta-input-tokens"
                        >

                          {
                            message.metadata
                              ?.input_tokens
                          }

                        </span>

                      </span>


                      <span className="meta-chip">

                        Output:{" "}

                        <span
                          data-testid=
                            "meta-output-tokens"
                        >

                          {
                            message.metadata
                              ?.output_tokens
                          }

                        </span>

                      </span>


                    </div>

                  </div>

                </div>

              )}


              {/* ERROR */}

              {message.role === "error" && (

                <div className="error-message">

                  <div className="message-label">
                    Error
                  </div>

                  <div className=
                    "bubble error-bubble"
                  >

                    {message.content}

                  </div>

                </div>

              )}

            </div>

          ))}


          {/* LOADING */}

          {loading && (

            <div className="assistant-message">

              <div className="message-label">

                ✦ Lyftr AI

              </div>


              <div className=
                "bubble assistant-bubble loading"
              >

                <span />
                <span />
                <span />

              </div>

            </div>

          )}


          <div ref={bottomRef} />


        </section>

      </main>


      {/* MESSAGE INPUT */}

      <footer className="composer-wrapper">

        <div className="composer">

          <textarea

            data-testid="chat-input"

            value={input}

            maxLength={4000}

            onChange={(event) =>
              setInput(
                event.target.value
              )
            }

            onKeyDown={handleKeyDown}

            placeholder=
              "Ask Lyftr AI anything..."

            rows={1}

          />


          <div className="composer-bottom">


            <span className="counter">

              {input.length}/4000

            </span>


            <button

              data-testid="send-button"

              onClick={handleSend}

              disabled={
                loading ||
                !input.trim()
              }

            >

              {loading
                ? "Thinking..."
                : "Send"}

            </button>


          </div>

        </div>

      </footer>

    </div>

  );
}


export default App;