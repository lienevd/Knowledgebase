<?php

use Ibc\ApiException;
use Ibc\DocumentStore;
use Ibc\Mailer;
use Ibc\RequestHelper;

$payload = json_decode((string) file_get_contents('php://input'), true) ?: [];

$documentIds = $payload['document_ids'] ?? [];
$keyword = $payload['keyword'] ?? '';
$requestOwnerEmail = RequestHelper::cleanEmailAddress($payload['request_owner_email'] ?? null);
$requesterEmail = RequestHelper::cleanRequiredEmailAddress($payload['requester_email'] ?? null, 'Requester');
$requestMessage = RequestHelper::cleanRequestMessage($payload['request_message'] ?? null);

if (empty($documentIds)) {
    throw new ApiException(400, 'No documents selected');
}

$requestedDocuments = [];
foreach ($documentIds as $documentId) {
    $document = DocumentStore::getDocument($documentId);
    if ($document) {
        $requestedDocuments[] = [
            'document_id' => $documentId,
            'filename' => $document['filename'] ?? 'Unknown',
        ];
    }
}

if (empty($requestedDocuments)) {
    throw new ApiException(404, 'No selected documents were found');
}

Mailer::sendEmail(
    $requestOwnerEmail,
    RequestHelper::requestEmailSubject(count($requestedDocuments)),
    RequestHelper::buildRequestEmailBody($requestedDocuments, $keyword, $requestMessage, $requesterEmail),
    $requesterEmail
);

foreach ($requestedDocuments as $requestedDocument) {
    RequestHelper::saveDownloadRequest(
        $requestedDocument['document_id'],
        $keyword,
        $requestedDocument['filename'],
        $requestMessage,
        $requesterEmail
    );
}

return [
    'status' => 'requested',
    'message' => count($requestedDocuments) . ' document request(s) emailed to ' . $requestOwnerEmail . '.',
    'requested_documents' => $requestedDocuments,
];
