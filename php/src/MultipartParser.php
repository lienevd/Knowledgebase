<?php

namespace Ibc;

/**
 * PHP's $_FILES superglobal silently keeps only the LAST part when multiple
 * multipart/form-data parts share the same field name without a "[]" suffix
 * (confirmed empirically: two parts named "files" -> $_FILES has one entry).
 * app.js sends exactly that shape (FormData.append('files', file) repeated,
 * no brackets) because Starlette/FastAPI handles repeated names natively.
 * Since app.js cannot be changed, this parses the raw request body itself so
 * every "files" part survives. Requires enable_post_data_reading=0 (set via
 * .htaccess/.user.ini) so php://input still holds the raw multipart body.
 */
class MultipartParser
{
    /**
     * @return array<int, array{filename: string, content: string}>
     */
    public static function parseFilesField(string $fieldName): array
    {
        $contentType = $_SERVER['CONTENT_TYPE'] ?? '';
        if (!str_contains($contentType, 'multipart/form-data')) {
            return [];
        }

        if (!preg_match('/boundary=(?:"([^"]+)"|([^;]+))/', $contentType, $m)) {
            return [];
        }
        $boundary = $m[1] !== '' ? $m[1] : $m[2];
        $boundary = trim($boundary);

        $raw = file_get_contents('php://input');
        if ($raw === false || $raw === '') {
            return [];
        }

        $results = [];
        $delimiter = '--' . $boundary;
        $rawParts = explode($delimiter, $raw);

        foreach ($rawParts as $part) {
            $part = ltrim($part, "\r\n");
            if ($part === '' || str_starts_with($part, '--')) {
                continue;
            }

            $separatorPos = strpos($part, "\r\n\r\n");
            if ($separatorPos === false) {
                continue;
            }

            $headerBlock = substr($part, 0, $separatorPos);
            $body = substr($part, $separatorPos + 4);
            $body = preg_replace('/\r\n$/', '', $body);

            if (!preg_match('/name="([^"]*)"/', $headerBlock, $nameMatch) || $nameMatch[1] !== $fieldName) {
                continue;
            }

            if (!preg_match('/filename="([^"]*)"/', $headerBlock, $filenameMatch)) {
                continue;
            }

            $results[] = [
                'filename' => $filenameMatch[1],
                'content' => $body,
            ];
        }

        return $results;
    }
}
