<?php

namespace Ibc;

/**
 * Port of src/classification/classifier.py
 */
class Classifier
{
    /**
     * @param array<string, string[]> $keywordMap
     * @return array{category: string, scores: array<string, int>, matched_keywords: array<string, array<string, int>>}
     */
    public static function classifyDocument(string $text, array $keywordMap): array
    {
        $scores = [];
        $matchedKeywords = [];
        $textLower = strtolower($text);

        foreach ($keywordMap as $category => $keywords) {
            foreach ($keywords as $keyword) {
                $count = substr_count($textLower, strtolower($keyword));
                if ($count > 0) {
                    $scores[$category] = ($scores[$category] ?? 0) + $count;
                    $matchedKeywords[$category][$keyword] = $count;
                }
            }
        }

        $bestCategory = 'Uncategorized';
        $bestCount = 0;
        foreach ($scores as $category => $count) {
            if ($count > $bestCount) {
                $bestCategory = $category;
                $bestCount = $count;
            }
        }

        return [
            'category' => $bestCategory,
            'scores' => $scores,
            'matched_keywords' => $matchedKeywords,
        ];
    }
}
