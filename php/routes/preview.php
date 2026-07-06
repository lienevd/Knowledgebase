<?php

use Ibc\ApiException;
use Ibc\DocumentStore;
use Ibc\Search;

$documentId = $_GET['document_id'] ?? '';
$document = DocumentStore::getDocument($documentId);
if (!$document) {
    throw new ApiException(404, 'Document not found');
}

$text = Search::readDocumentText($document);
$summaryKeywords = !empty($document['summary_keywords'])
    ? $document['summary_keywords']
    : Search::firstSummaryKeywords($document['keyword_scores'] ?? []);
$summary = Search::summarizeText($text, $document['category'] ?? '', $summaryKeywords);

return [
    'document_id' => $documentId,
    'filename' => $document['filename'] ?? 'Unknown',
    'category' => Search::displayCategory($document['category'] ?? null),
    'summary' => $summary,
    'summary_keywords' => $summaryKeywords,
    'source_character_count' => mb_strlen(Search::normalizeDocumentText($text), 'UTF-8'),
];
