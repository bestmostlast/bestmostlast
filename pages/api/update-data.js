import { google } from "googleapis";
import fs from "fs";
import path from "path";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const { GOOGLE_SHEETS_ID, GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_PRIVATE_KEY } = process.env;

  if (!GOOGLE_SHEETS_ID || !GOOGLE_SERVICE_ACCOUNT_EMAIL || !GOOGLE_PRIVATE_KEY) {
    return res.status(500).json({ error: "Missing Google Sheets env vars" });
  }

  try {
    const auth = new google.auth.JWT(
      GOOGLE_SERVICE_ACCOUNT_EMAIL,
      null,
      GOOGLE_PRIVATE_KEY.replace(/\\n/g, "\n"),
      ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    );

    const sheets = google.sheets({ version: "v4", auth });
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: GOOGLE_SHEETS_ID,
      range: "Sheet1",
    });

    const rows = response.data.values;
    if (!rows || rows.length === 0) return res.status(200).json({ message: "No data" });

    const csv = rows.map((r) => r.join(",")).join("\n");
    const filePath = path.join(process.cwd(), "public", "data", "premier-league.csv");
    fs.writeFileSync(filePath, csv);

    res.status(200).json({ message: "Updated", rows: rows.length - 1 });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
