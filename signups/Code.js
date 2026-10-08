// cecilylowe.com newsletter sign-ups. Runs in Cecily's own Google account (Apps Script web app).
// The site's sign-up line posts here. Each new address is added to the Google Sheet
// "cecilylowe.com newsletter" in her Drive, and she gets an email from newsletter@cecilylowe.com
// (a verified Gmail "Send mail as" alias) listing the ten most recent sign-ups. Replies go to Yale.

const TO = "cecily.lowe@yale.edu";
const FROM = "newsletter@cecilylowe.com";
const SHEET_NAME = "cecilylowe.com newsletter";

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.company) return reply_({ ok: true });                       // spam trap filled in: ignore quietly
  const email = String(p.email || "").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return reply_({ ok: false, error: "email" });

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const sheet = sheet_();
    const rows = sheet.getLastRow() > 1 ? sheet.getRange(2, 1, sheet.getLastRow() - 1, 2).getValues() : [];
    if (rows.some((r) => String(r[0]).toLowerCase() === email)) return reply_({ ok: true, already: true });
    const at = new Date();
    sheet.appendRow([email, at]);
    rows.push([email, at]);
    notify_(email, at, rows);
    return reply_({ ok: true });
  } finally {
    lock.releaseLock();
  }
}

function doGet() { return reply_({ ok: true, service: "cecilylowe.com newsletter" }); }

function sheet_() {
  const props = PropertiesService.getScriptProperties();
  let id = props.getProperty("SHEET_ID");
  let ss = id ? SpreadsheetApp.openById(id) : null;
  if (!ss) {
    ss = SpreadsheetApp.create(SHEET_NAME);
    props.setProperty("SHEET_ID", ss.getId());
    const s = ss.getSheets()[0];
    s.setName("Subscribers");
    s.appendRow(["email", "signed up"]);
    s.setFrozenRows(1);
  }
  return ss.getSheetByName("Subscribers") || ss.getSheets()[0];
}

function when_(d) { return Utilities.formatDate(new Date(d), "America/New_York", "MMM d, yyyy, h:mm a"); }
function esc_(v) { return String(v).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]); }

function notify_(email, at, rows) {
  const total = rows.length;
  const recent = rows.slice().sort((a, b) => new Date(b[1]) - new Date(a[1])).slice(0, 10);
  const label = total + " " + (total === 1 ? "person" : "people") + " total";
  const text = email + " joined your newsletter on " + when_(at) + ".\n\n" + label + "\n\n" +
    recent.map((r, i) => (i + 1) + ". " + r[0] + "  (" + when_(r[1]) + ")").join("\n") + "\n";
  const font = "font-family:Helvetica,Arial,sans-serif;";
  const list = recent.map((r, i) =>
    '<tr><td style="' + font + 'font-size:14px;line-height:20px;color:#999;padding:7px 12px 7px 0;border-top:1px solid #e6e6e6;width:24px;">' + (i + 1) + '</td>' +
    '<td style="' + font + 'font-size:14px;line-height:20px;color:#111;padding:7px 12px 7px 0;border-top:1px solid #e6e6e6;">' + esc_(r[0]) + '</td>' +
    '<td style="' + font + 'font-size:13px;line-height:20px;color:#999;padding:7px 0;border-top:1px solid #e6e6e6;text-align:right;white-space:nowrap;">' + esc_(when_(r[1])) + '</td></tr>').join("");
  const html =
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fff;"><tr><td style="padding:40px 24px;">' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;">' +
    '<tr><td style="' + font + 'font-size:20px;line-height:26px;color:#111;padding-bottom:6px;">' + esc_(email) + '</td></tr>' +
    '<tr><td style="' + font + 'font-size:14px;line-height:20px;color:#555;padding-bottom:36px;">joined your newsletter on ' + esc_(when_(at)) + '.</td></tr>' +
    '<tr><td style="' + font + 'font-size:13px;line-height:18px;color:#999;padding-bottom:10px;">' + label + '</td></tr>' +
    '<tr><td><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' + list + '</table></td></tr>' +
    '<tr><td style="' + font + 'font-size:12px;line-height:18px;color:#bbb;padding-top:36px;">cecilylowe.com</td></tr>' +
    '</table></td></tr></table>';
  GmailApp.sendEmail(TO, email + " joined your newsletter", text,
    { htmlBody: html, from: FROM, name: "Cecily Lowe", replyTo: TO });
}

function reply_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Run once by hand from the editor to grant permissions (Sheets + Gmail) and create the sheet.
function setup() {
  const s = sheet_();
  Logger.log("Sheet ready: " + s.getParent().getUrl());
  Logger.log("Aliases this Gmail can send as: " + GmailApp.getAliases().join(", "));
}
