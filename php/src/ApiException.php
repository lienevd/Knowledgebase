<?php

namespace Ibc;

/**
 * Mirrors FastAPI's HTTPException(status_code, detail) so route handlers can
 * throw and have a single top-level handler emit {"detail": "..."} with the
 * matching HTTP status, exactly like app.py's error responses.
 */
class ApiException extends \RuntimeException
{
    public function __construct(private readonly int $statusCode, string $detail)
    {
        parent::__construct($detail);
    }

    public function getStatusCode(): int
    {
        return $this->statusCode;
    }
}
