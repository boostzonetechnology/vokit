import { formatMoneyMinor } from "@/features/dashboard/lib/format";
import { formatWhen } from "@/features/payouts/lib/display";
import type { PayoutReceipt } from "@/features/payouts/types";

function receiptFileStem(receipt: PayoutReceipt): string {
  const ref = (receipt.receipt_number || receipt.payout_id || "receipt")
    .replaceAll(/[^a-zA-Z0-9-_]/g, "-")
    .slice(0, 48);
  return `vokit-payout-receipt-${ref}`;
}

/** Map common Unicode to Helvetica-safe ASCII (avoids "?" artifacts). */
function ascii(value: string): string {
  return value
    .replaceAll("\u2014", "-")
    .replaceAll("\u2013", "-")
    .replaceAll("\u00B7", "|")
    .replaceAll("\u2022", "*")
    .replaceAll("\u2018", "'")
    .replaceAll("\u2019", "'")
    .replaceAll("\u201C", '"')
    .replaceAll("\u201D", '"')
    .normalize("NFKD")
    .replaceAll(/[^\x20-\x7E]/g, "");
}

function pdfText(value: string): string {
  return ascii(value)
    .replaceAll("\\", "\\\\")
    .replaceAll("(", "\\(")
    .replaceAll(")", "\\)");
}

function dash(value?: string | null): string {
  const text = (value ?? "").trim();
  return text || "-";
}

function receiptFields(receipt: PayoutReceipt): Array<{ label: string; value: string }> {
  const agency = receipt.agency_display_name || receipt.agency_legal_name || "Agency";
  return [
    { label: "Receipt number", value: dash(receipt.receipt_number) },
    { label: "Agency", value: agency },
    { label: "Payout request ID", value: dash(receipt.payout_id) },
    { label: "Currency", value: receipt.currency || "USD" },
    { label: "Payout method", value: dash(receipt.method_label) },
    { label: "Requested", value: formatWhen(receipt.requested_at) },
    { label: "Paid", value: formatWhen(receipt.paid_at) },
    { label: "Status", value: (receipt.status || "paid").toUpperCase() },
    { label: "Transaction reference", value: dash(receipt.transaction_ref) },
    { label: "Issuer", value: receipt.issuer || "Vokit" },
  ];
}

function wrapDisclaimer(text: string, maxChars: number): string[] {
  const words = ascii(text).split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) lines.push(current);
  return lines;
}

/** Professional single-page payout receipt PDF (no extra dependency). */
function buildPayoutReceiptPdfBytes(receipt: PayoutReceipt): Uint8Array {
  const amount = formatMoneyMinor(receipt.amount_minor ?? 0, receipt.currency || "USD");
  const fields = receiptFields(receipt);
  const disclaimer =
    receipt.disclaimer ||
    "This receipt confirms payout processing and is not the underlying banking proof.";
  const disclaimerLines = wrapDisclaimer(disclaimer, 78);

  const ops: string[] = [];

  // Outer frame
  ops.push("0.82 0.84 0.86 RG", "1.5 w", "40 40 532 712 re", "S");

  // Header band
  ops.push("0.96 0.97 0.98 rg", "48 700 516 44 re", "f");
  ops.push("0.82 0.84 0.86 RG", "0.8 w", "48 700 516 0 m", "564 700 l", "S");

  ops.push("BT");
  ops.push("/F2 9 Tf", "0.42 0.45 0.50 rg", "56 728 Td", "(VOKIT) Tj");
  ops.push("/F2 18 Tf", "0.07 0.09 0.15 rg", "0 -18 Td", "(Payout receipt) Tj");
  ops.push("ET");

  ops.push("BT", "/F1 9 Tf", "0.45 0.48 0.52 rg", "56 686 Td");
  ops.push("(Agency-visible confirmation  |  private admin proof excluded) Tj", "ET");

  // Amount box
  ops.push("0.97 0.98 0.99 rg", "56 628 480 42 re", "f");
  ops.push("0.82 0.84 0.86 RG", "1 w", "56 628 480 42 re", "S");
  ops.push("BT", "/F1 9 Tf", "0.45 0.48 0.52 rg", "68 654 Td", "(Amount paid) Tj");
  ops.push("/F2 20 Tf", "0.07 0.09 0.15 rg", "0 -20 Td", `(${pdfText(amount)}) Tj`, "ET");

  // Detail rows
  let y = 598;
  for (const field of fields) {
    ops.push("0.93 0.94 0.95 RG", "0.5 w", `56 ${y + 14} m`, `536 ${y + 14} l`, "S");
    ops.push("BT");
    ops.push("/F1 9 Tf", "0.45 0.48 0.52 rg", `56 ${y} Td`, `(${pdfText(field.label)}) Tj`);
    ops.push("/F2 10 Tf", "0.07 0.09 0.15 rg", `170 0 Td`, `(${pdfText(field.value)}) Tj`);
    ops.push("ET");
    y -= 26;
  }

  // Footer
  ops.push("0.82 0.84 0.86 RG", "0.8 w", `56 ${y + 8} m`, `536 ${y + 8} l`, "S");
  y -= 8;
  ops.push("BT", "/F1 8 Tf", "0.45 0.48 0.52 rg");
  disclaimerLines.forEach((line, index) => {
    if (index === 0) ops.push(`56 ${y} Td`, `(${pdfText(line)}) Tj`);
    else ops.push("0 -11 Td", `(${pdfText(line)}) Tj`);
  });
  ops.push("ET");

  const stream = ops.join("\n");
  const objects = [
    "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
    "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
    "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n",
    `4 0 obj\n<< /Length ${stream.length} >>\nstream\n${stream}\nendstream\nendobj\n`,
    "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    "6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n",
  ];

  let pdf = "%PDF-1.4\n";
  const offsets: number[] = [0];
  for (const object of objects) {
    offsets.push(pdf.length);
    pdf += object;
  }
  const xrefStart = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n`;
  pdf += "0000000000 65535 f \n";
  for (let i = 1; i < offsets.length; i += 1) {
    pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\n`;
  pdf += `startxref\n${xrefStart}\n%%EOF`;
  return new TextEncoder().encode(pdf);
}

/** Agency-visible payout receipt as a downloadable PDF file. */
export function downloadPayoutReceiptPdf(receipt: PayoutReceipt): void {
  const bytes = buildPayoutReceiptPdfBytes(receipt);
  const blob = new Blob([bytes], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${receiptFileStem(receipt)}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
