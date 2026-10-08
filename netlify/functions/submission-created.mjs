// Runs automatically every time a Netlify form is submitted (the file name is the trigger).
// For the "newsletter" form: remember the address, then email Cecily a plain note with the ten
// most recent sign-ups. Email goes out through Cecily's own Gmail (GMAIL_USER + GMAIL_APP_PASSWORD,
// set on the Netlify site), so no extra service or account is involved.
import { getStore } from "@netlify/blobs";
import nodemailer from "nodemailer";

const TO = "cecily.lowe@yale.edu";

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

  const user = process.env.GMAIL_USER, pass = process.env.GMAIL_APP_PASSWORD;
  if (!user || !pass) return new Response("saved; Gmail not configured, so no email");

  const recent = [...list].sort((a, b) => b.at.localeCompare(a.at)).slice(0, 10);
  const lines = recent.map((s, i) => `${String(i + 1).padStart(2, " ")}. ${s.email}  (${when(s.at)})`);
  const text =
    `${email} joined your newsletter on ${when(at)}.\n\n` +
    `${list.length} ${list.length === 1 ? "person" : "people"} total\n\n` +
    lines.join("\n") + "\n";
  const html = emailHtml({ email, at, recent, total: list.length });

  const mail = nodemailer.createTransport({ host: "smtp.gmail.com", port: 465, secure: true, auth: { user, pass } });
  // Sent through Cecily's Gmail as newsletter@cecilylowe.com (a verified "Send mail as" alias).
  // Replies go to her Yale inbox: the domain has no mailbox of its own.
  await mail.sendMail({ from: `Cecily Lowe <${process.env.MAIL_FROM || user}>`, replyTo: TO, to: TO, subject: `${email} joined your newsletter`, text, html });
  return new Response("sent");
};

// ---- the email itself: plain, black on white, the site's own spare style. Tables and inline styles
//      because email apps (Gmail, Outlook, Apple Mail) ignore most modern CSS.
const esc = (v) => String(v).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

export function emailHtml({ email, at, recent, total }) {
  const font = "font-family:Helvetica,Arial,sans-serif;";
  const rows = recent.map((s, i) => `
          <tr>
            <td style="${font}font-size:14px;line-height:20px;color:#999;padding:7px 12px 7px 0;border-top:1px solid #e6e6e6;width:24px;vertical-align:top;">${i + 1}</td>
            <td style="${font}font-size:14px;line-height:20px;color:#111;padding:7px 12px 7px 0;border-top:1px solid #e6e6e6;vertical-align:top;">${esc(s.email)}</td>
            <td style="${font}font-size:13px;line-height:20px;color:#999;padding:7px 0;border-top:1px solid #e6e6e6;text-align:right;white-space:nowrap;vertical-align:top;">${esc(when(s.at))}</td>
          </tr>`).join("");
  return `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light only"><title>${esc(email)} joined your newsletter</title></head>
<body style="margin:0;padding:0;background:#ffffff;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff;">
    <tr><td align="left" style="padding:40px 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;">
        <tr><td style="${font}font-size:20px;line-height:26px;color:#111;padding-bottom:6px;">${esc(email)}</td></tr>
        <tr><td style="${font}font-size:14px;line-height:20px;color:#555;padding-bottom:36px;">joined your newsletter on ${esc(when(at))}.</td></tr>
        <tr><td style="${font}font-size:13px;line-height:18px;color:#999;padding-bottom:10px;">${total} ${total === 1 ? "person" : "people"} total</td></tr>
        <tr><td>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">${rows}
          </table>
        </td></tr>
        <tr><td style="${font}font-size:12px;line-height:18px;color:#bbb;padding-top:36px;">cecilylowe.com</td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}
