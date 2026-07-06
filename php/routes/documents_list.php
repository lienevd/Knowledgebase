<?php

use Ibc\DocumentStore;
use Ibc\Search;

$documents = DocumentStore::getAllDocuments();
$documentList = [];

foreach ($documents as $documentId => $document) {
    $documentList[] = [
        'document_id' => (string) $documentId,
        'title' => $document['filename'] ?? 'Untitled document',
        'category' => Search::displayCategory($document['category'] ?? null),
    ];
}

usort($documentList, fn ($a, $b) => strcmp(
    mb_strtolower($a['title'], 'UTF-8'),
    mb_strtolower($b['title'], 'UTF-8')
));

return [
    'total_documents' => count($documentList),
    'documents' => $documentList,
];
