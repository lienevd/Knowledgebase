<?php

use Ibc\ApiException;
use Ibc\DocumentStore;

$documentId = $_GET['document_id'] ?? '';
$document = DocumentStore::getDocument($documentId);
if (!$document) {
    throw new ApiException(404, 'Document not found');
}

$filePath = $document['file_path'] ?? null;
if (!$filePath || !is_file($filePath)) {
    throw new ApiException(404, 'File not available');
}

$filename = $document['filename'] ?? 'document';

header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . addslashes($filename) . '"');
header('Content-Length: ' . filesize($filePath));
readfile($filePath);
