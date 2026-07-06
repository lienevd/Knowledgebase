<?php

declare(strict_types=1);

use Ibc\ApiException;

$method = $_SERVER['REQUEST_METHOD'];
$path = rtrim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?: '/', '/');
if ($path === '') {
    $path = '/';
}

// PHP's built-in dev server (php -S ... index.php) invokes this router for
// every request, unlike Apache, where .htaccess already lets real files
// (static/*, etc.) bypass index.php entirely. This mirrors that for local
// testing only; it never applies in production behind Apache.
if (PHP_SAPI === 'cli-server' && $path !== '/' && is_file(__DIR__ . $path)) {
    return false;
}

require __DIR__ . '/config.php';

try {
    if ($method === 'GET' && $path === '/') {
        header('Content-Type: text/html; charset=utf-8');
        require __DIR__ . '/routes/home.php';
        return;
    }

    if ($method === 'GET' && $path === '/documents-count') {
        sendJson(require __DIR__ . '/routes/documents_count.php');
        return;
    }

    if ($method === 'GET' && $path === '/documents') {
        sendJson(require __DIR__ . '/routes/documents_list.php');
        return;
    }

    if ($method === 'DELETE' && preg_match('#^/documents/([^/]+)$#', $path, $matches)) {
        $documentId = $matches[1];
        sendJson(require __DIR__ . '/routes/documents_delete.php');
        return;
    }

    if ($method === 'POST' && $path === '/upload') {
        sendJson(require __DIR__ . '/routes/upload.php');
        return;
    }

    if ($method === 'GET' && $path === '/search') {
        sendJson(require __DIR__ . '/routes/search.php');
        return;
    }

    if ($method === 'GET' && $path === '/preview') {
        sendJson(require __DIR__ . '/routes/preview.php');
        return;
    }

    if ($method === 'GET' && $path === '/download') {
        require __DIR__ . '/routes/download.php';
        return;
    }

    if ($method === 'POST' && $path === '/request-download') {
        sendJson(require __DIR__ . '/routes/request_download.php');
        return;
    }

    if ($method === 'POST' && $path === '/request-bulk-download') {
        sendJson(require __DIR__ . '/routes/request_bulk_download.php');
        return;
    }

    http_response_code(404);
    sendJson(['detail' => 'Not Found']);
} catch (ApiException $e) {
    http_response_code($e->getStatusCode());
    sendJson(['detail' => $e->getMessage()]);
} catch (\Throwable $e) {
    http_response_code(500);
    sendJson(['detail' => 'Internal Server Error']);
}

function sendJson(array $payload): void
{
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
}
