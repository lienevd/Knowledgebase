<?php

use Ibc\ApiException;
use Ibc\DocumentStore;

$document = DocumentStore::getDocument($documentId);
if (!$document) {
    throw new ApiException(404, 'Document not found');
}

$deleted = DocumentStore::deleteDocument($documentId);
if (!$deleted) {
    throw new ApiException(404, 'Document not found');
}

return [
    'status' => 'deleted',
    'message' => 'Document deleted.',
    'document_id' => $documentId,
    'filename' => $document['filename'] ?? 'Unknown',
];
