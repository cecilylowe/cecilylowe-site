// Runs automatically every time a Netlify form is submitted (the file name is the trigger).
// For the "newsletter" form: remember the address, then email Cecily a plain note with the ten
// most recent sign-ups. Email goes through Resend (RESEND_API_KEY, set on the Netlify site).
import { getStore } from "@netlify/blobs";

const TO = "cecily.lowe@yale.edu";
const FROM = "Newsletter <onboarding@resend.dev>";

const when = (iso) =>
  new Date(iso).toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short", day: "numeric", year: "numeric",
    hour: "numeric", minute: "2-digit",
  });

export default async (req) => {
  const { payload } = await req.json();
  if (payload?.form_name !== "newsletter") return new Response("not the newsletter form");

  const email = String(payload.data?.email || "").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return new Response("no email");

  const store = getStore("newsletter");
  const list = (await store.get("subscribers", { type: "json" })) || [];
  if (list.some((s) => s.email === email)) return new Response("already subscribed");
  const at = payload.created_at || new Date().toISOString();
  list.push({ email, at });
  await store.setJSON("subscribers", list);

  const key = process.env.RESEND_API_KEY;
  if (!key) return new Response("saved; no RESEND_API_KEY, so no email");

  const recent = [...list].sort((a, b) => b.at.localeCompare(a.at)).slice(0, 10);
  const lines = recent.map((s, i) => `${String(i + 1).padStart(2, " ")}. ${s.email}  (${when(s.at)})`);
  const text =
    `${email} joined your newsletter on ${when(at)}.\n\n` +
    `Most recent sign-ups (${list.length} in total):\n\n` +
    lines.join("\n") + "\n";

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from: FROM, to: [TO], subject: `${email} joined your newsletter`, text }),
  });
  return new Response(res.ok ? "sent" : `email failed: ${res.status} ${await res.text()}`);
};
