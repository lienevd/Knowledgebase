<?php

namespace Ibc;

use PHPMailer\PHPMailer\Exception as PHPMailerException;
use PHPMailer\PHPMailer\PHPMailer;

/**
 * Port of smtp_config()/send_email() in app.py (lines 240-282).
 */
class Mailer
{
    /** @return array<string, string> */
    public static function smtpConfig(): array
    {
        return [
            'host' => trim((string) getenv('SMTP_HOST')),
            'port' => trim((getenv('SMTP_PORT') ?: '587')),
            'username' => trim((string) getenv('SMTP_USERNAME')),
            'password' => trim((string) getenv('SMTP_PASSWORD')),
            'sender' => trim((string) getenv('SMTP_FROM')),
            'use_tls' => strtolower(trim((getenv('SMTP_USE_TLS') ?: 'true'))),
        ];
    }

    /**
     * @throws ApiException on missing config or send failure, mirroring the FastAPI HTTPException shapes.
     */
    public static function sendEmail(string $toEmail, string $subject, string $body, ?string $replyTo = null): void
    {
        $config = self::smtpConfig();
        $missing = array_values(array_filter(
            ['SMTP_HOST', 'SMTP_USERNAME', 'SMTP_PASSWORD', 'SMTP_FROM'],
            fn ($name) => !getenv($name)
        ));

        if (!empty($missing)) {
            throw new ApiException(
                503,
                'Email is not configured. Set ' . implode(', ', $missing) . ' before sending requests.'
            );
        }

        $mail = new PHPMailer(true);

        try {
            $mail->isSMTP();
            $mail->Host = $config['host'];
            $mail->Port = (int) ($config['port'] !== '' ? $config['port'] : 587);
            $mail->SMTPAuth = true;
            $mail->Username = $config['username'];
            $mail->Password = $config['password'];

            if (!in_array($config['use_tls'], ['0', 'false', 'no', 'off'], true)) {
                $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
            }

            $mail->Timeout = 20;
            $mail->CharSet = 'UTF-8';

            $mail->setFrom($config['sender']);
            $mail->addAddress($toEmail);
            if ($replyTo) {
                $mail->addReplyTo($replyTo);
            }

            $mail->Subject = $subject;
            $mail->isHTML(false);
            $mail->Body = $body;

            $mail->send();
        } catch (PHPMailerException|\Throwable $e) {
            throw new ApiException(502, 'Could not send request email: ' . $e->getMessage());
        }
    }
}
