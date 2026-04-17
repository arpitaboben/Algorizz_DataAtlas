import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const backendResp = await fetch(`${BACKEND_URL}/api/augment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!backendResp.ok) {
      const error = await backendResp.json().catch(() => ({ detail: 'Augmentation failed' }));
      return NextResponse.json(
        { message: error.detail || 'Augmentation failed' },
        { status: backendResp.status }
      );
    }

    const data = await backendResp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Augment proxy error:', error);
    return NextResponse.json(
      { message: 'Failed to connect to backend.' },
      { status: 502 }
    );
  }
}
