<?php

namespace Ibc;

/**
 * Port of src/storage/document_store.py
 */
class DocumentStore
{
    public static function dataDir(): string
    {
        return dirname(__DIR__) . '/data';
    }

    public static function storageFile(): string
    {
        return self::dataDir() . '/documents.json';
    }

    public static function uploadDir(): string
    {
        return self::dataDir() . '/uploads';
    }

    private static function ensureStorageDir(): void
    {
        if (!is_dir(self::dataDir())) {
            mkdir(self::dataDir(), 0775, true);
        }
    }

    private static function ensureUploadDir(): void
    {
        if (!is_dir(self::uploadDir())) {
            mkdir(self::uploadDir(), 0775, true);
        }
    }

    /** @return array<string, array> */
    public static function loadDocuments(): array
    {
        self::ensureStorageDir();
        $file = self::storageFile();
        if (is_file($file)) {
            $contents = file_get_contents($file);
            $decoded = json_decode($contents, true);
            return is_array($decoded) ? $decoded : [];
        }

        return [];
    }

    /** @param array<string, array> $documents */
    public static function saveDocuments(array $documents): void
    {
        self::ensureStorageDir();
        file_put_contents(
            self::storageFile(),
            json_encode($documents, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );
    }

    public static function saveUploadedFile(string $documentId, string $filename, string $fileBytes): string
    {
        self::ensureUploadDir();
        $safeName = $documentId . '_' . basename($filename);
        $uploadPath = self::uploadDir() . '/' . $safeName;
        file_put_contents($uploadPath, $fileBytes);

        return $uploadPath;
    }

    public static function resolveFilePath(string $documentId, string $filename, ?string $filePath = null): ?string
    {
        if ($filePath && is_file($filePath)) {
            return $filePath;
        }

        $fallback = self::uploadDir() . '/' . $documentId . '_' . basename($filename);
        if (is_file($fallback)) {
            return $fallback;
        }

        return null;
    }

    public static function storeDocument(
        string $documentId,
        string $filename,
        string $content,
        array $keywordScores,
        string $category = 'Uncategorized',
        ?string $filePath = null,
        array $categoryScores = [],
        array $matchedKeywords = [],
        array $indexEntries = [],
        array $summaryKeywords = []
    ): void {
        $documents = self::loadDocuments();
        $resolvedPath = self::resolveFilePath($documentId, $filename, $filePath);

        $documents[$documentId] = [
            'filename' => $filename,
            'content' => $content,
            'keyword_scores' => $keywordScores,
            'category' => $category,
            'file_path' => $resolvedPath,
            'category_scores' => $categoryScores,
            'matched_keywords' => $matchedKeywords,
            'index_entries' => $indexEntries,
            'index_results' => $indexEntries,
            'summary_keywords' => $summaryKeywords,
        ];

        self::saveDocuments($documents);
    }

    public static function getDocument(string $documentId): ?array
    {
        $documents = self::loadDocuments();
        $document = $documents[$documentId] ?? null;

        if ($document !== null && empty($document['file_path']) && !empty($document['filename'])) {
            $resolvedPath = self::resolveFilePath($documentId, $document['filename'], null);
            if ($resolvedPath) {
                $document['file_path'] = $resolvedPath;
                $documents[$documentId] = $document;
                self::saveDocuments($documents);
            }
        }

        return $document;
    }

    /** @return array<string, array> */
    public static function getAllDocuments(): array
    {
        $documents = self::loadDocuments();
        $activeDocuments = array_filter(
            $documents,
            fn ($document) => !self::isMissingUploadedFile($document)
        );

        if (count($activeDocuments) !== count($documents)) {
            self::saveDocuments($activeDocuments);
        }

        return $activeDocuments;
    }

    public static function isMissingUploadedFile(array $document): bool
    {
        $filePath = $document['file_path'] ?? null;

        return !empty($filePath) && !is_file($filePath);
    }

    public static function deleteUploadedFile(array $document): bool
    {
        $candidatePaths = [];

        if (!empty($document['file_path'])) {
            $candidatePaths[] = $document['file_path'];
        }

        $filename = $document['filename'] ?? null;
        $documentId = $document['document_id'] ?? null;
        if ($documentId && $filename) {
            $candidatePaths[] = self::uploadDir() . '/' . $documentId . '_' . basename($filename);
        }

        $uploadRoot = realpath(self::uploadDir());
        $deleted = false;

        foreach ($candidatePaths as $path) {
            $resolvedPath = realpath($path);
            if ($resolvedPath === false) {
                continue;
            }

            if ($uploadRoot !== false && str_starts_with($resolvedPath, $uploadRoot . DIRECTORY_SEPARATOR)) {
                unlink($resolvedPath);
                $deleted = true;
            }
        }

        return $deleted;
    }

    public static function deleteDocument(string $documentId): bool
    {
        $documents = self::loadDocuments();
        if (isset($documents[$documentId])) {
            $document = $documents[$documentId];
            $document['document_id'] = $documentId;
            self::deleteUploadedFile($document);
            unset($documents[$documentId]);
            self::saveDocuments($documents);

            return true;
        }

        return false;
    }
}
