<?php

namespace Ibc;

/**
 * Port of the download-request helpers in app.py (lines 186-317):
 * save_download_request, clean_email_address, clean_required_email_address,
 * clean_request_message, build_request_email_body, request_email_subject.
 */
class RequestHelper
{
    private static function requestsFile(): string
    {
        return DocumentStore::dataDir() . '/download_requests.json';
    }

    public static function saveDownloadRequest(
        string $documentId,
        ?string $keyword,
        ?string $filename,
        ?string $requestMessage,
        ?string $requesterEmail
    ): void {
        $dir = DocumentStore::dataDir();
        if (!is_dir($dir)) {
            mkdir($dir, 0775, true);
        }

        $file = self::requestsFile();
        $requests = [];
        if (is_file($file)) {
            $decoded = json_decode((string) file_get_contents($file), true);
            $requests = is_array($decoded) ? $decoded : [];
        }

        $now = \DateTime::createFromFormat('U.u', sprintf('%.6F', microtime(true)), new \DateTimeZone('UTC'));

        $requests[] = [
            'document_id' => $documentId,
            'filename' => $filename ?: 'Unknown',
            'keyword' => $keyword ?: '',
            'requester_email' => $requesterEmail ?: '',
            'request_message' => $requestMessage ?: '',
            'requested_at' => $now->format('Y-m-d\TH:i:s.u') . 'Z',
            'status' => 'pending',
        ];

        file_put_contents(
            $file,
            json_encode($requests, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );
    }

    public static function cleanEmailAddress(?string $value): string
    {
        $email = trim($value ?? '');
        if ($email === '') {
            return DEFAULT_REQUEST_OWNER_EMAIL;
        }

        if (!preg_match('/^[^@\s]+@[^@\s]+\.[^@\s]+$/', $email)) {
            throw new ApiException(400, 'Request owner email is invalid');
        }

        return $email;
    }

    public static function cleanRequiredEmailAddress(?string $value, string $label): string
    {
        $email = trim($value ?? '');
        if ($email === '') {
            throw new ApiException(400, "{$label} email is required");
        }

        if (!preg_match('/^[^@\s]+@[^@\s]+\.[^@\s]+$/', $email)) {
            throw new ApiException(400, "{$label} email is invalid");
        }

        return $email;
    }

    public static function cleanRequestMessage(?string $value): string
    {
        return mb_substr(trim($value ?? ''), 0, 1200, 'UTF-8');
    }

    /** @param array<int, array{filename: string}> $documents */
    public static function buildRequestEmailBody(
        array $documents,
        ?string $keyword = null,
        ?string $requestMessage = null,
        ?string $requesterEmail = null
    ): string {
        $requestedAt = gmdate('Y-m-d H:i:s') . ' UTC';
        $lines = [$requestedAt, $requesterEmail ?: 'No requester email provided', ''];

        if ($requestMessage) {
            $lines[] = $requestMessage;
            $lines[] = '';
        }

        if ($keyword) {
            $lines[] = "Search keyword: {$keyword}";
            $lines[] = '';
        }

        $lines[] = 'Requested documents:';
        foreach ($documents as $item) {
            $lines[] = '- ' . ($item['filename'] ?? 'Unknown');
        }

        return implode("\n", $lines);
    }

    public static function requestEmailSubject(int $documentCount): string
    {
        if ($documentCount === 1) {
            return 'Document request: 1 document';
        }

        return "Document request: {$documentCount} documents";
    }
}
