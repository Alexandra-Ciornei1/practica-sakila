import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(req) {
  try {
    const body = await req.json();
    const question = body.question;

    // Trimitem cererea la backend-ul Python
    const res = await axios.post('http://127.0.0.1:8000/ask', { question });
    return NextResponse.json(res.data);
  } catch (error) {
    console.error('Backend error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
