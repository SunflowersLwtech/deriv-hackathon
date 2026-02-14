"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import type { DerivAccount } from "@/lib/api";

const DERIV_APP_ID = process.env.NEXT_PUBLIC_DERIV_APP_ID || "125719";
const DERIV_OAUTH_URL =
  process.env.NEXT_PUBLIC_DERIV_OAUTH_URL ||
  "https://oauth.deriv.com/oauth2/authorize";

export function useDerivAuth() {
  const [accounts, setAccounts] = useState<DerivAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const oauthStartedRef = useRef(false);

  const defaultAccount = accounts.find((a) => a.is_default) ?? null;

  const fetchAccounts = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getDerivAccounts();
      const list = data.accounts || [];
      setAccounts(list);
      setIsConnected(list.length > 0);
    } catch {
      setAccounts([]);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  const connect = useCallback(() => {
    // Guard against accidental double-clicks / double-invocations.
    if (oauthStartedRef.current) return;
    oauthStartedRef.current = true;

    const redirectUri =
      process.env.NEXT_PUBLIC_DERIV_REDIRECT_URI?.trim() ||
      `${window.location.origin}/auth/deriv/callback`;

    // Always pass redirect_uri so Deriv doesn't fall back to a stale URL
    // configured in the Deriv developer console.
    const url = new URL(DERIV_OAUTH_URL);
    url.searchParams.set("app_id", String(DERIV_APP_ID));
    url.searchParams.set("redirect_uri", redirectUri);
    url.searchParams.set("l", "en");
    url.searchParams.set("brand", "deriv");

    window.location.assign(url.toString());
  }, []);

  const disconnect = useCallback(
    async (accountId: string) => {
      await api.deleteDerivAccount(accountId);
      await fetchAccounts();
    },
    [fetchAccounts]
  );

  const setDefault = useCallback(
    async (accountId: string) => {
      await api.setDefaultDerivAccount(accountId);
      await fetchAccounts();
    },
    [fetchAccounts]
  );

  return {
    isConnected,
    accounts,
    defaultAccount,
    connect,
    disconnect,
    setDefault,
    isLoading,
    refresh: fetchAccounts,
  };
}
