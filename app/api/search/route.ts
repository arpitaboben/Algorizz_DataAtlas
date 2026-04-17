import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Proxy to FastAPI backend
    const backendResp = await fetch(`${BACKEND_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!backendResp.ok) {
      const error = await backendResp.json().catch(() => ({ detail: 'Backend request failed' }));
      return NextResponse.json(
        { message: error.detail || 'Search failed' },
        { status: backendResp.status }
      );
    }

    const data = await backendResp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Search proxy error:', error);
    return NextResponse.json(
      { message: 'Failed to connect to backend. Is the FastAPI server running on port 8000?' },
      { status: 502 }
    );
  }
}
