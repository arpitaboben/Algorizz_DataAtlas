import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const resolvedParams = await params;
    const { id } = resolvedParams;

    // Fetch from FastAPI backend
    const backendResp = await fetch(`${BACKEND_URL}/api/dataset/${id}`, {
      headers: { 'Content-Type': 'application/json' },
    });

    if (!backendResp.ok) {
      const error = await backendResp.json().catch(() => ({ detail: 'Dataset not found' }));
      return NextResponse.json(
        { message: error.detail || 'Dataset not found' },
        { status: backendResp.status }
      );
    }

    const data = await backendResp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Dataset proxy error:', error);
    return NextResponse.json(
      { message: 'Failed to connect to backend.' },
      { status: 502 }
    );
  }
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const resolvedParams = await params;
    const body = await request.json();

    // Proxy analyze request to FastAPI backend
    const backendResp = await fetch(`${BACKEND_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: resolvedParams.id,
        ...body,
      }),
    });

    if (!backendResp.ok) {
      const error = await backendResp.json().catch(() => ({ detail: 'Analysis failed' }));
      return NextResponse.json(
        { message: error.detail || 'Analysis failed' },
        { status: backendResp.status }
      );
    }

    const data = await backendResp.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Analyze proxy error:', error);
    return NextResponse.json(
      { message: 'Failed to connect to backend.' },
      { status: 502 }
    );
  }
}
