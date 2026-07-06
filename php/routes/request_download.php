<?php

use Ibc\ApiException;
use Ibc\DocumentStore;
use Ibc\Mailer;
use Ibc\RequestHelper;

$payload = json_decode((string) file_get_contents('php://input'), true) ?: [];

$documentId = $payload['document_id'] ?? null;
$keyword = $payload['keyword'] ?? null;
$requestOwnerEmail = RequestHelper::cleanEmailAddress($payload['request_owner_email'] ?? null);
$requesterEmail = RequestHelper::cleanRequiredEmailAddress($payload['requester_email'] ?? null, 'Requester');
$requestMessage = RequestHelper::cleanRequestMessage($payload['request_message'] ?? null);

if (!$documentId) {
    throw new ApiException(400, 'Document ID is required');
}

$document = DocumentStore::getDocument($documentId);
if (!$document) {
    throw new ApiException(404, 'Document not found');
}

$requestedDocuments = [[
    'document_id' => $documentId,
    'filename' => $document['filename'] ?? 'Unknown',
]];

Mailer::sendEmail(
    $requestOwnerEmail,
    RequestHelper::requestEmailSubject(count($requestedDocuments)),
    RequestHelper::buildRequestEmailBody($requestedDocuments, $keyword, $requestMessage, $requesterEmail),
    $requesterEmail
);

RequestHelper::saveDownloadRequest($documentId, $keyword, $document['filename'] ?? null, $requestMessage, $requesterEmail);

return [
    'status' => 'requested',
    'message' => "Your download request has been emailed to {$requestOwnerEmail}.",
    'document_name' => $document['filename'] ?? null,
];
