<?php

use Ibc\Classifier;
use Ibc\DocumentStore;
use Ibc\Extractor;
use Ibc\MultipartParser;
use Ibc\Search;
use Ibc\Uuid;

$keywordMap = $GLOBALS['KEYWORD_MAP'];

$files = MultipartParser::parseFilesField('files');

// Fallback for hosts where enable_post_data_reading couldn't be disabled:
// $_FILES still works correctly for a single uploaded file.
if (empty($files) && !empty($_FILES['files'])) {
    $f = $_FILES['files'];
    if (is_array($f['name'])) {
        foreach ($f['name'] as $i => $name) {
            if (($f['error'][$i] ?? UPLOAD_ERR_NO_FILE) === UPLOAD_ERR_OK) {
                $files[] = [
                    'filename' => $name,
                    'content' => (string) file_get_contents($f['tmp_name'][$i]),
                ];
            }
        }
    } elseif (($f['error'] ?? UPLOAD_ERR_NO_FILE) === UPLOAD_ERR_OK) {
        $files[] = [
            'filename' => $f['name'],
            'content' => (string) file_get_contents($f['tmp_name']),
        ];
    }
}

$uploadedFiles = [];
$skippedFiles = [];

foreach ($files as $file) {
    $filename = $file['filename'];

    try {
        $contentBytes = $file['content'];
        $documentId = Uuid::v4();
        $filePath = DocumentStore::saveUploadedFile($documentId, $filename, $contentBytes);
        $extractedText = trim(Extractor::extractText($filePath));

        if ($extractedText === '') {
            $extractedText = trim(Extractor::decodeLenient($contentBytes));
        }

        if ($extractedText === '') {
            throw new \RuntimeException('No text could be extracted from this file.');
        }

        $classification = Classifier::classifyDocument($extractedText, $keywordMap);
        $category = $classification['category'] ?? 'Uncategorized';
        $categoryKeywords = $keywordMap[$category] ?? [];
        $extractedTextLower = mb_strtolower($extractedText, 'UTF-8');

        $keywordScores = [];
        foreach ($categoryKeywords as $keyword) {
            $count = substr_count($extractedTextLower, mb_strtolower($keyword, 'UTF-8'));
            if ($count > 0) {
                $keywordScores[$keyword] = $count;
            }
        }

        $indexEntries = Search::buildIndexEntries($filename, $extractedText, $category, $keywordScores);
        $summaryKeywords = Search::firstSummaryKeywords($keywordScores);

        DocumentStore::storeDocument(
            $documentId,
            $filename,
            $extractedText,
            $keywordScores,
            $category,
            $filePath,
            $classification['scores'] ?? [],
            $classification['matched_keywords'] ?? [],
            $indexEntries,
            $summaryKeywords
        );

        $uploadedFiles[] = $filename;
    } catch (\Throwable $exc) {
        $skippedFiles[] = "{$filename} ({$exc->getMessage()})";
    }
}

return [
    'uploaded_count' => count($uploadedFiles),
    'uploaded_files' => $uploadedFiles,
    'skipped_files' => $skippedFiles,
];
