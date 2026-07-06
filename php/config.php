<?php

declare(strict_types=1);

use Ibc\KeywordLoader;
use Ibc\Search;

require __DIR__ . '/vendor/autoload.php';

// Optional local .env for dev/hosting environments where you can't set real
// environment variables (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
// SMTP_FROM, SMTP_USE_TLS, REQUEST_OWNER_EMAIL).
$envFile = __DIR__ . '/.env';
if (is_file($envFile)) {
    foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#') || !str_contains($line, '=')) {
            continue;
        }
        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value);
        if (getenv($key) === false) {
            putenv("{$key}={$value}");
        }
    }
}

define('BASE_DIR', __DIR__);
define('UPLOAD_DIR', BASE_DIR . '/data/uploads');
define('REQUESTS_FILE', BASE_DIR . '/data/download_requests.json');
define('DEFAULT_REQUEST_OWNER_EMAIL', getenv('REQUEST_OWNER_EMAIL') ?: 's.e.vdongen@gmail.com');

$GLOBALS['KEYWORDS'] = KeywordLoader::loadKeywords();
$GLOBALS['KEYWORD_MAP'] = KeywordLoader::loadKeywordCategories();

$keywordExamples = !empty($GLOBALS['KEYWORDS'])
    ? array_slice($GLOBALS['KEYWORDS'], 0, 8)
    : ['security', 'risk', 'authentication', 'encryption', 'cloud'];
$GLOBALS['KEYWORD_EXAMPLES'] = $keywordExamples;

if (empty($GLOBALS['KEYWORD_MAP'])) {
    $GLOBALS['KEYWORD_MAP'] = ['Security & Risk' => $keywordExamples];
}

Search::init($GLOBALS['KEYWORD_MAP']);
