<?php

use Ibc\ApiException;
use Ibc\Search;

$keyword = trim($_GET['keyword'] ?? '');
if ($keyword === '') {
    throw new ApiException(400, 'Keyword cannot be empty');
}

return Search::searchDocumentsByKeyword($keyword);
