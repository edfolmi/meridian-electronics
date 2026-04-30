import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const body = await request.text();

  try {
    const response = await fetch(`${backendBaseUrl}/api/auth/sign-in`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const responseBody = await response.text();
    return new NextResponse(responseBody, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the authentication service." },
      { status: 503 },
    );
  }
}

