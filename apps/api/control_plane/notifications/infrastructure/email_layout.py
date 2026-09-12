from __future__ import annotations

import html


def wrap_email_html(
    *,
    title: str,
    message: str,
    greeting: str = "Hi there!",
    cta_url: str = "",
    cta_label: str = "",
    footer_name: str = "The Vokit Team",
) -> str:
    """Shared transactional HTML shell used for every outbound Vokit email."""
    safe_title = html.escape(title)
    safe_greeting = html.escape(greeting)
    safe_footer = html.escape(footer_name)
    safe_cta_label = html.escape(cta_label or "Open Vokit")
    # Message may already contain escaped placeholders from render_template.
    paragraphs = [
        part.strip()
        for part in message.replace("\r\n", "\n").split("\n")
        if part.strip()
    ]
    body_html = "".join(
        f'<p style="margin:0 0 12px;font-size:16px;line-height:1.55;color:#4b5563;">'
        f"{paragraph}</p>"
        for paragraph in paragraphs
    ) or (
        '<p style="margin:0 0 12px;font-size:16px;line-height:1.55;color:#4b5563;">'
        f"{html.escape(message)}</p>"
    )

    cta_block = ""
    if cta_url:
        safe_url = html.escape(cta_url, quote=True)
        cta_block = f"""
          <tr>
            <td align="center" style="padding:8px 0 28px;">
              <a href="{safe_url}"
                 style="display:inline-block;background:#6557f5;color:#ffffff;
                        font-size:16px;font-weight:700;text-decoration:none;
                        padding:14px 28px;border-radius:999px;">
                {safe_cta_label}
              </a>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 0 24px;font-size:12px;line-height:1.5;color:#9ca3af;">
              If the button does not work, copy and paste this link into your browser:<br/>
              <a href="{safe_url}" style="color:#6557f5;word-break:break-all;">{safe_url}</a>
            </td>
          </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{safe_title}</title>
</head>
<body style="margin:0;padding:0;background:#f3f4f6;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
               style="max-width:560px;background:#ffffff;border-radius:16px;padding:40px 32px;">
          <tr>
            <td align="center" style="padding-bottom:20px;">
              <div style="width:42px;height:42px;border-radius:999px;background:#6557f5;
                          color:#ffffff;font-family:Arial,Helvetica,sans-serif;font-size:20px;
                          font-weight:700;line-height:42px;text-align:center;">v</div>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <svg width="88" height="72" viewBox="0 0 88 72" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <rect x="10" y="18" width="60" height="42" rx="6" fill="#e5e7eb"/>
                <path d="M10 26 L40 46 L70 26" fill="none" stroke="#d1d5db" stroke-width="4"/>
                <circle cx="64" cy="22" r="14" fill="#22c55e"/>
                <path d="M57 22 L62 27 L72 16" fill="none" stroke="#ffffff" stroke-width="3"
                      stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-bottom:18px;font-family:Arial,Helvetica,sans-serif;
                                       font-size:28px;font-weight:700;color:#111827;letter-spacing:-0.02em;">
              {safe_title}
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-bottom:10px;font-family:Arial,Helvetica,sans-serif;
                                       font-size:16px;font-weight:700;color:#111827;">
              {safe_greeting}
            </td>
          </tr>
          <tr>
            <td align="center" style="padding-bottom:8px;font-family:Arial,Helvetica,sans-serif;">
              {body_html}
            </td>
          </tr>
          {cta_block}
          <tr>
            <td align="center" style="padding-top:8px;font-family:Arial,Helvetica,sans-serif;
                                       font-size:14px;line-height:1.5;color:#9ca3af;">
              Thanks,<br/>{safe_footer}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def greeting_from_email(email: str) -> str:
    local = (email or "").split("@", 1)[0].strip()
    if not local:
        return "Hi there!"
    label = local.replace(".", " ").replace("_", " ").strip()
    if not label:
        return "Hi there!"
    return f"Hi {label.title()}!"
