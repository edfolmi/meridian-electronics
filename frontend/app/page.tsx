"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import {
  Loader2,
  LogIn,
  SendHorizontal,
  ShieldCheck,
  ShoppingCart,
} from "lucide-react";
import styles from "./page.module.css";

type Role = "user" | "assistant";

type Message = {
  id: string;
  role: Role;
  content: string;
  toolCalls?: ToolCall[];
};

type ToolCall = {
  name: string;
  ok: boolean;
  latency_ms: number;
};

type CustomerSession = {
  customer_id: string;
  name: string;
  email: string;
  role?: string | null;
};

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");

const starterPrompts = [
  "Do you have any 27 inch monitors in stock?",
  "Can you show my recent orders?",
  "I want to place an order for a monitor.",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi, I can help with Meridian product availability, customer authentication, orders, and order history.",
    },
  ]);
  const [input, setInput] = useState("");
  const [customer, setCustomer] = useState<CustomerSession | null>(null);
  const [authEmail, setAuthEmail] = useState("");
  const [authPin, setAuthPin] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const chatMessages = useMemo(
    () =>
      messages
        .filter((message) => message.id !== "welcome")
        .map((message) => ({
          role: message.role,
          content: message.content,
        })),
    [messages],
  );

  async function sendMessage(content: string) {
    const trimmed = content.trim();
    if (!trimmed || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [
            ...chatMessages,
            { role: userMessage.role, content: userMessage.content },
          ],
          customer,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "The support service is unavailable.");
      }

      const data: {
        message: string;
        request_id: string;
        tool_calls: ToolCall[];
      } = await response.json();

      setMessages((current) => [
        ...current,
        {
          id: data.request_id,
          role: "assistant",
          content: data.message,
          toolCalls: data.tool_calls,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(input);
  }

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSigningIn) {
      return;
    }

    setAuthError(null);
    setIsSigningIn(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/sign-in`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, pin: authPin }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "Could not sign in.");
      }

      const data: { customer: CustomerSession; message: string } =
        await response.json();
      setCustomer(data.customer);
      setAuthPin("");
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `You are signed in as ${data.customer.name}. I can now help with account-specific support.`,
        },
      ]);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Could not sign in.");
    } finally {
      setAuthPin("");
      setIsSigningIn(false);
    }
  }

  return (
    <main className={styles.shell}>
      <section className={styles.chatPanel} aria-labelledby="page-title">
        <header className={styles.header}>
          <div>
            <p className={styles.eyebrow}>Meridian Electronics</p>
            <h1 className={styles.title} id="page-title">
              Support chat
            </h1>
          </div>
          <div className={styles.status}>
            <ShieldCheck aria-hidden="true" size={18} />
            {customer ? `Signed in: ${customer.name}` : "MCP-backed"}
          </div>
        </header>

        <div className={styles.messages} aria-live="polite">
          {messages.map((message) => (
            <article
              className={`${styles.message} ${styles[message.role]}`}
              key={message.id}
            >
              <p>{message.content}</p>
              {message.toolCalls && message.toolCalls.length > 0 ? (
                <div className={styles.toolRow} aria-label="Verified tool calls">
                  {message.toolCalls.map((toolCall, index) => (
                    <span
                      className={toolCall.ok ? styles.toolOk : styles.toolError}
                      key={`${toolCall.name}-${index}`}
                    >
                      {toolCall.name}
                    </span>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
          {isLoading ? (
            <article className={`${styles.message} ${styles.assistant}`}>
              <span className={styles.loadingText}>
                <Loader2 aria-hidden="true" className={styles.spin} size={17} />
                Checking Meridian systems
              </span>
            </article>
          ) : null}
        </div>

        <div className={styles.authAndStarters}>
          {!customer ? (
            <form className={styles.authForm} onSubmit={handleSignIn}>
              <div className={styles.authHeader}>
                <LogIn aria-hidden="true" size={17} />
                Secure sign-in for orders and account support
              </div>
              <label>
                Email
                <input
                  autoComplete="email"
                  disabled={isSigningIn}
                  onChange={(event) => setAuthEmail(event.target.value)}
                  required
                  type="email"
                  value={authEmail}
                />
              </label>
              <label>
                PIN
                <input
                  autoComplete="current-password"
                  disabled={isSigningIn}
                  inputMode="numeric"
                  maxLength={12}
                  minLength={4}
                  onChange={(event) => setAuthPin(event.target.value)}
                  required
                  type="password"
                  value={authPin}
                />
              </label>
              <button disabled={isSigningIn} type="submit">
                {isSigningIn ? (
                  <Loader2 aria-hidden="true" className={styles.spin} size={16} />
                ) : (
                  <LogIn aria-hidden="true" size={16} />
                )}
                Sign in
              </button>
              {authError ? <p className={styles.authError}>{authError}</p> : null}
            </form>
          ) : null}

          <div className={styles.starters}>
            {starterPrompts.map((prompt) => (
              <button
                disabled={isLoading}
                key={prompt}
                onClick={() => void sendMessage(prompt)}
                type="button"
              >
                <ShoppingCart aria-hidden="true" size={16} />
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {error ? <p className={styles.error}>{error}</p> : null}

        <form className={styles.composer} onSubmit={handleSubmit}>
          <textarea
            aria-label="Message"
            disabled={isLoading}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about products, orders, or your account"
            ref={inputRef}
            rows={2}
            value={input}
          />
          <button aria-label="Send message" disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <Loader2 aria-hidden="true" className={styles.spin} size={20} />
            ) : (
              <SendHorizontal aria-hidden="true" size={20} />
            )}
          </button>
        </form>
      </section>
    </main>
  );
}
