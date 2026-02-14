"use client";

import { createContext, useContext } from "react";
import {
  useStreamingChat,
  type UseStreamingChatReturn,
} from "@/hooks/useStreamingChat";

const ChatContext = createContext<UseStreamingChatReturn | null>(null);

export function useChatContext(): UseStreamingChatReturn {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChatContext must be used within ChatProvider");
  return ctx;
}

export default function ChatProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const chat = useStreamingChat();
  return <ChatContext.Provider value={chat}>{children}</ChatContext.Provider>;
}
