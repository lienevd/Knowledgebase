<?php

use Ibc\DocumentStore;

return ['total_documents' => count(DocumentStore::getAllDocuments())];
