<?php

namespace Ibc;

/**
 * Port of src/keywords/keyword_loader.py
 */
class KeywordLoader
{
    public static function keywordFile(): string
    {
        return dirname(__DIR__) . '/data/IT_Security_Keywords.csv';
    }

    public static function normalizeKeyword(string $rawValue): string
    {
        $term = strtolower(trim($rawValue));

        while ($term !== '' && ctype_digit($term[0])) {
            $term = substr($term, 1);
        }

        return ltrim($term, ". ");
    }

    public static function normalizeCategory(string $rawValue): string
    {
        $term = self::normalizeKeyword($rawValue);

        return ucwords($term, " \t\r\n\f\v-'");
    }

    /**
     * @return array<string, string[]>
     */
    public static function loadKeywordCategories(): array
    {
        $file = self::keywordFile();

        if (!is_file($file)) {
            return [];
        }

        $rows = [];
        $handle = fopen($file, 'r');
        if ($handle === false) {
            return [];
        }

        while (($row = fgetcsv($handle, 0, ';')) !== false) {
            $rows[] = $row;
        }
        fclose($handle);

        if (empty($rows)) {
            return [];
        }

        $categories = array_map(
            fn ($cell) => self::normalizeCategory((string) $cell),
            $rows[0]
        );

        $keywordMap = [];
        $seenByCategory = [];
        foreach ($categories as $category) {
            if ($category !== '') {
                $keywordMap[$category] = [];
                $seenByCategory[$category] = [];
            }
        }

        for ($r = 1; $r < count($rows); $r++) {
            $row = $rows[$r];
            foreach ($row as $index => $cell) {
                if ($index >= count($categories)) {
                    continue;
                }

                $category = $categories[$index];
                if ($category === '') {
                    continue;
                }

                $term = self::normalizeKeyword((string) $cell);
                if ($term !== '' && !isset($seenByCategory[$category][$term])) {
                    $seenByCategory[$category][$term] = true;
                    $keywordMap[$category][] = $term;
                }
            }
        }

        return array_filter($keywordMap, fn ($keywords) => !empty($keywords));
    }

    /**
     * @return string[]
     */
    public static function loadKeywords(): array
    {
        $keywords = [];
        $seen = [];

        foreach (self::loadKeywordCategories() as $categoryKeywords) {
            foreach ($categoryKeywords as $term) {
                if ($term !== '' && !isset($seen[$term])) {
                    $seen[$term] = true;
                    $keywords[] = $term;
                }
            }
        }

        return $keywords;
    }
}
