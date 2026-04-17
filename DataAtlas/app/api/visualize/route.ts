import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const backendResp = await fetch(`${BACKEND_URL}/api/visualize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!backendResp.ok) {
      const error = await backendResp.json().catch(() => ({ detail: 'Visualization failed' }));
      return NextResponse.json(
        { message: error.detail || 'Visualization failed' },
        { status: backendResp.status }
      );
    }

    const data = await backendResp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Visualize proxy error:', error);
    return NextResponse.json(
      { message: 'Failed to connect to backend.' },
      { status: 502 }
    );
  }
}
