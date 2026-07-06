<?php

namespace Ibc;

/**
 * Port of the search / snippet / summary logic in app.py (lines ~407-731).
 */
class Search
{
    /** @var array<string, string[]> */
    private static array $keywordMap = [];

    /** @var array<string, string[]> */
    private static array $keywordToCategories = [];

    private static ?array $searchTextCache = null;
    private static bool $searchTextCacheChanged = false;

    private const DEFAULT_CATEGORY_RULES = [
        'Security' => ['security', 'threat', 'breach', 'vulnerability', 'malware', 'attack'],
        'Risk' => ['risk', 'exposure', 'compliance', 'governance', 'audit'],
        'Authentication' => ['authentication', 'auth', 'login', 'password', 'credential'],
        'Encryption' => ['encryption', 'crypto', 'ssl', 'tls', 'cipher'],
        'Cloud' => ['cloud', 'azure', 'aws', 'gcp'],
        'Privacy' => ['privacy', 'personal', 'data protection', 'gdpr'],
    ];

    private const STOP_WORDS = [
        'about', 'after', 'also', 'and', 'are', 'because', 'been', 'but', 'can',
        'for', 'from', 'has', 'have', 'into', 'its', 'may', 'not', 'our', 'that',
        'the', 'their', 'there', 'these', 'this', 'those', 'was', 'were', 'will',
        'with', 'within', 'you', 'your',
    ];

    /** @param array<string, string[]> $keywordMap */
    public static function init(array $keywordMap): void
    {
        self::$keywordMap = $keywordMap;
        self::$keywordToCategories = [];

        foreach ($keywordMap as $categoryName => $categoryKeywords) {
            foreach ($categoryKeywords as $keywordValue) {
                $normalized = KeywordLoader::normalizeKeyword($keywordValue);
                self::$keywordToCategories[$normalized][] = $categoryName;
            }
        }
    }

    private static function cacheFile(): string
    {
        return DocumentStore::dataDir() . '/search_text_cache.json';
    }

    public static function displayCategory(?string $category): string
    {
        if (!$category || $category === 'Uncategorized') {
            return 'Uncategorized';
        }

        return KeywordLoader::normalizeCategory($category);
    }

    public static function countKeywordOccurrences(?string $text, string $keyword): int
    {
        $cleanKeyword = mb_strtolower(trim($keyword), 'UTF-8');
        if ($cleanKeyword === '') {
            return 0;
        }

        return self::mbSubstrCount(mb_strtolower($text ?? '', 'UTF-8'), $cleanKeyword);
    }

    private static function mbSubstrCount(string $haystack, string $needle): int
    {
        if ($needle === '') {
            return 0;
        }

        $count = 0;
        $offset = 0;
        $needleLen = mb_strlen($needle, 'UTF-8');
        while (($pos = mb_strpos($haystack, $needle, $offset, 'UTF-8')) !== false) {
            $count++;
            $offset = $pos + $needleLen;
        }

        return $count;
    }

    /** @return int[] character offsets of every (case-insensitive) occurrence */
    private static function findAllOffsets(string $haystack, string $needle): array
    {
        $offsets = [];
        if ($needle === '') {
            return $offsets;
        }

        $needleLen = mb_strlen($needle, 'UTF-8');
        $offset = 0;
        while (($pos = mb_stripos($haystack, $needle, $offset, 'UTF-8')) !== false) {
            $offsets[] = $pos;
            $offset = $pos + $needleLen;
        }

        return $offsets;
    }

    public static function normalizeDocumentText(?string $text): string
    {
        return trim(preg_replace('/\s+/u', ' ', $text ?? ''));
    }

    public static function extractKeywordContext(?string $text, string $keyword, int $contextLength = 150): string
    {
        $content = $text ?? '';
        $keywordLower = mb_strtolower(trim($keyword), 'UTF-8');
        $matchIndex = mb_stripos($content, $keywordLower, 0, 'UTF-8');

        if ($matchIndex === false) {
            return '';
        }

        $contentLen = mb_strlen($content, 'UTF-8');
        $start = max(0, $matchIndex - $contextLength);
        $end = min($contentLen, $matchIndex + mb_strlen($keywordLower, 'UTF-8') + $contextLength);
        $context = self::normalizeDocumentText(mb_substr($content, $start, $end - $start, 'UTF-8'));

        if ($start > 0) {
            $context = '...' . $context;
        }
        if ($end < $contentLen) {
            $context = $context . '...';
        }

        return $context;
    }

    /** @return string[] */
    public static function extractKeywordSnippets(
        ?string $text,
        string $keyword,
        int $contextLength = 32,
        int $maxSnippets = 25
    ): array {
        $cleanKeyword = trim($keyword);
        if ($cleanKeyword === '') {
            return [];
        }

        $content = $text ?? '';
        $contentLen = mb_strlen($content, 'UTF-8');
        $keywordLen = mb_strlen($cleanKeyword, 'UTF-8');
        $snippets = [];

        foreach (self::findAllOffsets($content, $cleanKeyword) as $matchStart) {
            $matchEnd = $matchStart + $keywordLen;
            $start = max(0, $matchStart - $contextLength);
            $end = min($contentLen, $matchEnd + $contextLength);
            $snippet = self::normalizeDocumentText(mb_substr($content, $start, $end - $start, 'UTF-8'));

            if ($start > 0) {
                $snippet = '...' . $snippet;
            }
            if ($end < $contentLen) {
                $snippet = $snippet . '...';
            }

            $snippets[] = $snippet;
            if (count($snippets) >= $maxSnippets) {
                break;
            }
        }

        return $snippets;
    }

    /**
     * @param array<string, int> $keywordScores
     * @return array<int, array{Filename: string, Keyword: string, Category: string, Snippet: string}>
     */
    public static function buildIndexEntries(string $filename, ?string $text, string $category, array $keywordScores): array
    {
        $entries = [];

        foreach (array_keys($keywordScores) as $keyword) {
            foreach (self::extractKeywordSnippets($text, $keyword) as $snippet) {
                $entries[] = [
                    'Filename' => $filename,
                    'Keyword' => $keyword,
                    'Category' => $category,
                    'Snippet' => $snippet,
                ];
            }
        }

        return $entries;
    }

    /** @param array<string, int> $keywordScores */
    public static function firstSummaryKeywords(array $keywordScores, int $limit = 10): array
    {
        $entries = array_filter($keywordScores, fn ($count) => $count > 0);
        $keys = array_keys($entries);

        usort($keys, function ($a, $b) use ($entries) {
            $countCompare = $entries[$b] <=> $entries[$a];
            if ($countCompare !== 0) {
                return $countCompare;
            }

            return strcmp(mb_strtolower($a, 'UTF-8'), mb_strtolower($b, 'UTF-8'));
        });

        return array_slice($keys, 0, $limit);
    }

    public static function isSearchableStoredText(?string $text): bool
    {
        if ($text === null || trim($text) === '') {
            return false;
        }

        $sample = mb_substr($text, 0, 2000, 'UTF-8');
        if (str_starts_with(ltrim($sample), '%PDF-')) {
            return false;
        }

        $length = max(mb_strlen($sample, 'UTF-8'), 1);
        $controlChars = 0;
        for ($i = 0, $n = strlen($sample); $i < $n; $i++) {
            $ord = ord($sample[$i]);
            if ($ord < 32 && !in_array($sample[$i], ["\r", "\n", "\t"], true)) {
                $controlChars++;
            }
        }

        return ($controlChars / $length) < 0.02;
    }

    /** @return array<string, string> */
    private static function loadSearchTextCache(): array
    {
        if (self::$searchTextCache !== null) {
            return self::$searchTextCache;
        }

        $file = self::cacheFile();
        if (is_file($file)) {
            $decoded = json_decode((string) file_get_contents($file), true);
            self::$searchTextCache = is_array($decoded) ? $decoded : [];
        } else {
            self::$searchTextCache = [];
        }

        return self::$searchTextCache;
    }

    private static function saveSearchTextCache(): void
    {
        if (!self::$searchTextCacheChanged) {
            return;
        }

        $dir = DocumentStore::dataDir();
        if (!is_dir($dir)) {
            mkdir($dir, 0775, true);
        }

        file_put_contents(
            self::cacheFile(),
            json_encode(self::loadSearchTextCache(), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
        );
        self::$searchTextCacheChanged = false;
    }

    private static function documentCacheKey(array $document): ?string
    {
        $filePath = $document['file_path'] ?? null;
        if (!$filePath || !is_file($filePath)) {
            return null;
        }

        $resolved = realpath($filePath);
        $size = filesize($filePath);
        $mtimeNs = (int) filemtime($filePath) * 1_000_000_000;

        return "{$resolved}|{$size}|{$mtimeNs}";
    }

    public static function readDocumentText(array $document): string
    {
        $filePath = $document['file_path'] ?? null;

        if ($filePath && is_file($filePath)) {
            $extracted = trim(Extractor::extractText($filePath));
            if ($extracted !== '') {
                return $extracted;
            }

            $suffix = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));
            if (in_array($suffix, ['txt', 'md', 'html', 'htm'], true)) {
                $raw = file_get_contents($filePath);
                return trim($raw === false ? '' : $raw);
            }
        }

        return trim($document['content'] ?? '');
    }

    public static function getSearchableDocumentText(array $document): string
    {
        $storedText = $document['content'] ?? '';
        if (self::isSearchableStoredText($storedText)) {
            return $storedText;
        }

        $cacheKey = self::documentCacheKey($document);
        $cache = self::loadSearchTextCache();
        if ($cacheKey && isset($cache[$cacheKey])) {
            return $cache[$cacheKey];
        }

        $extractedText = self::readDocumentText($document);
        if ($cacheKey && self::isSearchableStoredText($extractedText)) {
            self::$searchTextCache[$cacheKey] = $extractedText;
            self::$searchTextCacheChanged = true;
        }

        return $extractedText;
    }

    /** @param array<int, array{keyword_count:int, filename:string}> $results */
    public static function sortResultsByKeywordCount(array $results): array
    {
        usort($results, function ($a, $b) {
            $countCompare = $b['keyword_count'] <=> $a['keyword_count'];
            if ($countCompare !== 0) {
                return $countCompare;
            }

            return strcmp(mb_strtolower($a['filename'], 'UTF-8'), mb_strtolower($b['filename'], 'UTF-8'));
        });

        return $results;
    }

    /** @return string[] */
    public static function categoriesForSearchKeyword(string $keyword): array
    {
        $normalized = KeywordLoader::normalizeKeyword($keyword);

        return self::$keywordToCategories[$normalized] ?? [];
    }

    public static function indexedKeywordResult(string $documentId, array $document, string $keyword): ?array
    {
        $normalizedQuery = KeywordLoader::normalizeKeyword($keyword);
        $storedEntries = $document['index_results'] ?? ($document['index_entries'] ?? []);

        $entries = array_values(array_filter($storedEntries, function ($entry) use ($normalizedQuery) {
            $keywordValue = $entry['Keyword'] ?? ($entry['keyword'] ?? '');
            return KeywordLoader::normalizeKeyword($keywordValue) === $normalizedQuery;
        }));

        if (empty($entries)) {
            return null;
        }

        $keywordScores = $document['keyword_scores'] ?? [];
        $indexedKeyword = $entries[0]['Keyword'] ?? ($entries[0]['keyword'] ?? '');
        $count = $keywordScores[$indexedKeyword] ?? count($entries);

        return [
            'document_id' => $documentId,
            'filename' => $document['filename'] ?? 'Unknown',
            'keyword_count' => $count,
            'category' => self::displayCategory($document['category'] ?? null),
            'context' => $entries[0]['Snippet'] ?? ($entries[0]['snippet'] ?? ''),
        ];
    }

    public static function searchDocumentsByKeyword(string $keyword, int $limit = 10): array
    {
        $results = [];
        $targetCategories = self::categoriesForSearchKeyword($keyword);

        foreach (DocumentStore::getAllDocuments() as $documentId => $document) {
            $documentCategory = $document['category'] ?? null;
            if (
                !empty($targetCategories)
                && $documentCategory !== null
                && array_key_exists($documentCategory, self::$keywordMap)
                && !in_array($documentCategory, $targetCategories, true)
            ) {
                continue;
            }

            $indexedResult = self::indexedKeywordResult((string) $documentId, $document, $keyword);
            if ($indexedResult) {
                $results[] = $indexedResult;
                continue;
            }

            $text = self::getSearchableDocumentText($document);
            $count = self::countKeywordOccurrences($text, $keyword);

            if ($count <= 0) {
                continue;
            }

            $results[] = [
                'document_id' => (string) $documentId,
                'filename' => $document['filename'] ?? 'Unknown',
                'keyword_count' => $count,
                'category' => self::displayCategory($document['category'] ?? null),
                'context' => self::extractKeywordContext($text, $keyword),
            ];
        }

        $results = self::sortResultsByKeywordCount($results);
        self::saveSearchTextCache();

        $limitedResults = array_slice($results, 0, $limit);

        return [
            'keyword' => $keyword,
            'total_matches' => count($results),
            'displayed_matches' => count($limitedResults),
            'result_limit' => $limit,
            'searched_categories' => array_values($targetCategories),
            'top_document' => $limitedResults[0] ?? null,
            'all_results' => array_values($limitedResults),
        ];
    }

    /** @return string[] */
    public static function splitSentences(?string $text): array
    {
        $clean = self::normalizeDocumentText($text);
        if ($clean === '') {
            return [];
        }

        $sentences = preg_split('/(?<=[.!?])\s+(?=[A-Z0-9])/u', $clean);

        return array_values(array_filter(array_map('trim', $sentences), function ($sentence) {
            $len = mb_strlen($sentence, 'UTF-8');
            return $len >= 40 && $len <= 520;
        }));
    }

    /** @return string[] */
    public static function meaningfulTerms(string $text, int $limit = 18): array
    {
        $stopSet = array_flip(self::STOP_WORDS);
        preg_match_all('/[A-Za-z][A-Za-z\-]{3,}/', mb_strtolower($text, 'UTF-8'), $matches);

        $counts = [];
        foreach ($matches[0] as $word) {
            if (!isset($stopSet[$word])) {
                $counts[$word] = ($counts[$word] ?? 0) + 1;
            }
        }

        arsort($counts);

        return array_slice(array_keys($counts), 0, $limit);
    }

    public static function summarizeText(
        ?string $text,
        string $category = '',
        ?array $priorityKeywords = null,
        int $maxChars = 520
    ): string {
        $clean = self::normalizeDocumentText($text);
        if ($clean === '') {
            return 'No readable content was found for this document.';
        }

        $sentences = self::splitSentences($clean);
        if (empty($sentences)) {
            return self::truncateOnWordBoundary($clean, $maxChars);
        }

        $priorityTerms = array_slice(array_values(array_filter(
            array_map(fn ($k) => mb_strtolower(trim((string) $k), 'UTF-8'), $priorityKeywords ?? []),
            fn ($k) => $k !== ''
        )), 0, 10);

        $importantTerms = array_flip(!empty($priorityTerms) ? $priorityTerms : self::meaningfulTerms($clean));
        $categoryTerms = self::$keywordMap[$category] ?? (self::DEFAULT_CATEGORY_RULES[$category] ?? []);

        $bestScore = null;
        $bestIndex = null;
        $bestSentence = '';

        foreach ($sentences as $index => $sentence) {
            $sentenceLower = mb_strtolower($sentence, 'UTF-8');
            preg_match_all('/[A-Za-z][A-Za-z\-]{3,}/', $sentenceLower, $wordMatches);
            $termHits = 0;
            foreach ($wordMatches[0] as $word) {
                if (isset($importantTerms[$word])) {
                    $termHits++;
                }
            }

            $priorityHits = 0;
            foreach ($priorityTerms as $term) {
                $priorityHits += self::mbSubstrCount($sentenceLower, $term);
            }

            $categoryHits = 0;
            foreach ($categoryTerms as $term) {
                $categoryHits += self::mbSubstrCount($sentenceLower, mb_strtolower($term, 'UTF-8'));
            }

            $sentenceLen = mb_strlen($sentence, 'UTF-8');
            $lengthScore = ($sentenceLen >= 80 && $sentenceLen <= 260) ? 1 : 0;
            $positionScore = max(0, 3 - $index * 0.15);
            $score = ($priorityHits * 4) + $termHits + ($categoryHits * 2) + $lengthScore + $positionScore;

            if ($bestScore === null || $score > $bestScore) {
                $bestScore = $score;
                $bestIndex = $index;
                $bestSentence = $sentence;
            }
        }

        $summary = $bestSentence;
        if (mb_strlen($summary, 'UTF-8') > $maxChars) {
            $summary = self::truncateOnWordBoundary($summary, $maxChars);
        }

        return $summary;
    }

    private static function truncateOnWordBoundary(string $text, int $maxChars): string
    {
        $originalLen = mb_strlen($text, 'UTF-8');
        $truncated = mb_substr($text, 0, $maxChars, 'UTF-8');
        $lastSpace = mb_strrpos($truncated, ' ', 0, 'UTF-8');
        $base = $lastSpace !== false ? mb_substr($truncated, 0, $lastSpace, 'UTF-8') : $truncated;

        return $base . ($originalLen > $maxChars ? '...' : '');
    }
}
