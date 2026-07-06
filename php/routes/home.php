<?php

$keywords = $GLOBALS['KEYWORDS'];
$keywordHint = implode(', ', array_map(
    fn ($kw) => '<strong>' . $kw . '</strong>',
    $GLOBALS['KEYWORD_EXAMPLES']
));
$requestOwnerEmail = DEFAULT_REQUEST_OWNER_EMAIL;

require __DIR__ . '/../templates/index.php';
