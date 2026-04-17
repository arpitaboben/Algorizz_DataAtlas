import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();

    // Forward multipart form data to FastAPI backend
    const backendResp = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!backendResp.ok) {
      const error = await backendResp.json().catch(() => ({ detail: 'Upload failed' }));
      return NextResponse.json(
        { message: error.detail || 'Upload failed' },
        { status: backendResp.status }
      );
    }

    const data = await backendResp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Upload proxy error:', error);
    return NextResponse.json(
      { message: 'Failed to connect to backend. Is the FastAPI server running?' },
      { status: 502 }
    );
  }
}
