from __future__ import annotations

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import settings

logger = logging.getLogger("auth.email")


class EmailService:
    @staticmethod
    def send_verification_email(email: str, name: str, otp_code: str, verify_link: str) -> bool:
        """Mengirimkan email verifikasi berisi kode OTP dan tautan konfirmasi akun."""
        subject = f"[{settings.APP_NAME}] Kode Verifikasi Pendaftaran Akun"
        
        body_text = f"""Halo {name},

Terima kasih telah mendaftar di {settings.APP_NAME}.

Kode OTP verifikasi akun Anda adalah: {otp_code}
(Kode ini berlaku selama {settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES} menit).

Atau Anda dapat mengonfirmasi langsung melalui tautan berikut:
{verify_link}

Jika Anda tidak merasa mendaftar di sistem kami, silakan abaikan email ini.
"""

        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
            <h2 style="color: #0f172a; margin-top: 0;">Verifikasi Alamat Email Anda</h2>
            <p style="color: #475569; font-size: 15px; line-height: 1.5;">Halo <strong>{name}</strong>,</p>
            <p style="color: #475569; font-size: 14px; line-height: 1.5;">Gunakan kode OTP berikut untuk mengaktifkan akun pendaftaran Anda:</p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="display: inline-block; font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #1e3a8a; background: #eff6ff; padding: 12px 28px; border-radius: 8px; border: 1px dashed #3b82f6;">
                    {otp_code}
                </span>
            </div>
            <p style="color: #64748b; font-size: 13px;">Kode OTP ini berlaku selama <strong>{settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES} menit</strong> dan hanya dapat digunakan satu kali.</p>
            <div style="margin: 28px 0; text-align: center;">
                <a href="{verify_link}" style="background: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; display: inline-block;">
                    Verifikasi Akun Sekarang ➔
                </a>
            </div>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px; margin-bottom: 0;">Pesan ini dikirim otomatis oleh sistem {settings.APP_NAME}.</p>
        </div>
        """

        return EmailService._send_mail(email, subject, body_text, body_html)

    @staticmethod
    def send_password_reset_email(email: str, name: str, reset_link: str) -> bool:
        """Mengirimkan email tautan pemulihan kata sandi."""
        subject = f"[{settings.APP_NAME}] Permintaan Reset Kata Sandi"

        body_text = f"""Halo {name},

Kami menerima permintaan untuk mereset kata sandi akun Anda.
Silakan klik tautan di bawah ini untuk membuat kata sandi baru:
{reset_link}

Tautan ini berlaku selama {settings.PASSWORD_RESET_EXPIRE_MINUTES} menit dan hanya dapat digunakan sekali.

Jika Anda tidak meminta perubahan kata sandi, abaikan email ini dan akun Anda tetap aman.
"""

        body_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
            <h2 style="color: #0f172a; margin-top: 0;">Reset Kata Sandi Akun</h2>
            <p style="color: #475569; font-size: 15px; line-height: 1.5;">Halo <strong>{name}</strong>,</p>
            <p style="color: #475569; font-size: 14px; line-height: 1.5;">Klik tombol di bawah ini untuk membuat kata sandi baru akun Anda:</p>
            <div style="margin: 28px 0; text-align: center;">
                <a href="{reset_link}" style="background: #e11d48; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: bold; font-size: 14px; display: inline-block;">
                    Buat Kata Sandi Baru ➔
                </a>
            </div>
            <p style="color: #64748b; font-size: 13px;">Tautan ini berlaku selama <strong>{settings.PASSWORD_RESET_EXPIRE_MINUTES} menit</strong>.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
            <p style="color: #94a3b8; font-size: 12px; margin-bottom: 0;">Jika Anda tidak meminta reset password, abaikan pesan ini.</p>
        </div>
        """

        return EmailService._send_mail(email, subject, body_text, body_html)

    @staticmethod
    def _send_mail(to_email: str, subject: str, text_content: str, html_content: str) -> bool:
        """Mengirim email melalui SMTP atau mode simulasi jika belum ada SMTP credentials."""
        if settings.EMAIL_MOCK_MODE or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.info(f"[EMAIL MOCK] To: {to_email} | Subject: {subject}")
            print(f"\n==================== [SIMULASI EMAIL TERKIRIM] ====================")
            print(f"Kepada   : {to_email}")
            print(f"Subjek   : {subject}")
            print(f"Isi Pesan:\n{text_content}")
            print(f"===================================================================\n")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email

            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

            return True
        except Exception as e:
            logger.error(f"Gagal mengirim email ke {to_email}: {e}")
            return False
