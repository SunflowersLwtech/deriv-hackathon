import { NextResponse, type NextRequest } from "next/server";

/**
 * Deriv OAuth returns tokens in the query string (acct1/token1/cur1...).
 * If Deriv is configured to redirect to "/" (or any other path), we still
 * want to land on our dedicated callback page to process and store tokens.
 */
export function middleware(req: NextRequest) {
  const url = req.nextUrl;
  const hasDerivOAuthParams =
    url.searchParams.has("acct1") || url.searchParams.has("token1");

  if (hasDerivOAuthParams) {
    // Avoid redirect loops.
    if (!url.pathname.startsWith("/auth/deriv/callback")) {
      const dest = url.clone();
      dest.pathname = "/auth/deriv/callback";
      return NextResponse.redirect(dest);
    }
  }

  return NextResponse.next();
}

export const config = {
  // Avoid running middleware for Next.js internals and static assets.
  matcher: ["/((?!_next/|favicon.ico).*)"],
};

