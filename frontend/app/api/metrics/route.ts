import { NextResponse } from "next/server";
import path from "path";
import sqlite3 from "sqlite3";
import { open } from "sqlite";

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // Determine the absolute path to the SQLite database
    const dbPath = path.resolve(process.cwd(), "../backend/data/agrialert.db");

    // Open the database connection
    const db = await open({
      filename: dbPath,
      driver: sqlite3.Database,
    });

    // Run queries
    const totalCalls = await db.get(`SELECT COUNT(*) as count FROM call_analytics`);
    const successfulCalls = await db.get(`SELECT COUNT(*) as count FROM call_analytics WHERE outcome = 'success'`);
    const failedCalls = await db.get(`SELECT COUNT(*) as count FROM call_analytics WHERE outcome = 'failed'`);

    // Close the database
    await db.close();

    // Return the metrics
    return NextResponse.json({
      total: totalCalls.count || 0,
      successful: successfulCalls.count || 0,
      failed: failedCalls.count || 0,
    });
  } catch (error) {
    console.error("Database query failed:", error);
    // Return zeros if table doesn't exist yet or db fails
    return NextResponse.json({
      total: 0,
      successful: 0,
      failed: 0,
    });
  }
}
