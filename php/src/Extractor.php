<?php

namespace Ibc;

use Smalot\PdfParser\Parser as PdfParser;

/**
 * Port of src/processing/extractor.py
 */
class Extractor
{
    public static function extractText(string $filePath): string
    {
        $suffix = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));

        if ($suffix === 'pdf') {
            return self::extractPdf($filePath);
        }

        if ($suffix === 'txt' || $suffix === 'md') {
            return self::readTextLenient($filePath);
        }

        if ($suffix === 'docx') {
            return self::extractDocx($filePath);
        }

        if ($suffix === 'html' || $suffix === 'htm') {
            return self::extractHtml($filePath);
        }

        return '';
    }

    /**
     * No try/catch here on purpose: extractor.py's PDF branch has no
     * try/except around fitz.open() either, so a parse failure must
     * propagate and cause the upload to be skipped (with the real error
     * message), not silently fall back to dumping raw PDF bytes as "text".
     */
    private static function extractPdf(string $filePath): string
    {
        $parser = new PdfParser();
        $document = $parser->parseFile($filePath);
        $text = '';
        foreach ($document->getPages() as $page) {
            $text .= $page->getText();
        }

        return $text;
    }

    private static function extractDocx(string $filePath): string
    {
        try {
            $zip = new \ZipArchive();
            if ($zip->open($filePath) !== true) {
                return '';
            }

            $xml = $zip->getFromName('word/document.xml');
            $zip->close();

            if ($xml === false) {
                return '';
            }

            $dom = new \DOMDocument();
            $previous = libxml_use_internal_errors(true);
            $dom->loadXML($xml);
            libxml_use_internal_errors($previous);

            $xpath = new \DOMXPath($dom);
            $xpath->registerNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main');

            $paragraphs = [];
            foreach ($xpath->query('//w:p') as $paragraphNode) {
                $textNodes = $xpath->query('.//w:t', $paragraphNode);
                $paragraphText = '';
                foreach ($textNodes as $textNode) {
                    $paragraphText .= $textNode->textContent;
                }

                if ($paragraphText !== '') {
                    $paragraphs[] = $paragraphText;
                }
            }

            return implode("\n", $paragraphs);
        } catch (\Throwable $e) {
            return '';
        }
    }

    private static function extractHtml(string $filePath): string
    {
        $rawHtml = self::readTextLenient($filePath);
        $text = preg_replace('/<script[\s\S]*?<\/script>/i', ' ', $rawHtml);
        $text = preg_replace('/<style[\s\S]*?<\/style>/i', ' ', $text);
        $text = preg_replace('/<[^>]+>/', ' ', $text);

        return html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }

    private static function readTextLenient(string $filePath): string
    {
        $raw = file_get_contents($filePath);
        if ($raw === false) {
            return '';
        }

        return self::decodeLenient($raw);
    }

    /** Mirrors Python's bytes.decode(errors="ignore") for UTF-8 content. */
    public static function decodeLenient(string $bytes): string
    {
        $clean = @iconv('UTF-8', 'UTF-8//IGNORE', $bytes);

        return $clean === false ? $bytes : $clean;
    }
}
