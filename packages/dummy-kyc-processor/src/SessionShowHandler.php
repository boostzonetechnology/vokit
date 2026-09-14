<?php

declare(strict_types=1);

namespace Vokit\DummyKyc;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\UploadedFileInterface;

final class SessionShowHandler
{
    public function __construct(private readonly SessionStore $store)
    {
    }

    public function __invoke(
        ServerRequestInterface $request,
        ResponseInterface $response,
        array $args,
    ): ResponseInterface {
        $sessionId = (string) ($args['session_id'] ?? '');
        if (strtoupper($request->getMethod()) === 'POST') {
            $upload = $request->getUploadedFiles()['evidence'] ?? null;
            if ($upload instanceof UploadedFileInterface && $upload->getError() === UPLOAD_ERR_OK) {
                $this->store->storeUpload($sessionId, $upload);
            }
        }
        $html = $this->page($sessionId);
        $response->getBody()->write($html);
        return $response->withHeader('Content-Type', 'text/html; charset=utf-8');
    }

    private function page(string $sessionId): string
    {
        $safe = htmlspecialchars($sessionId, ENT_QUOTES, 'UTF-8');
        $items = '';
        foreach ($this->store->listFiles($sessionId) as $name) {
            $items .= '<li>' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</li>';
        }
        if ($items === '') {
            $items = '<li>No files yet. Uploads stay on this dummy server, not in Vokit.</li>';
        }
        return <<<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Vokit lab KYC</title>
</head>
<body>
  <h1>Dummy KYC processor</h1>
  <p>Lab host only. Review happens here. Vokit stores status, not document bytes.</p>
  <p>Session: {$safe}</p>
  <h2>Evidence on this server</h2>
  <ul>{$items}</ul>
  <form method="post" action="/session/{$safe}" enctype="multipart/form-data">
    <label>Upload dummy evidence
      <input type="file" name="evidence" required>
    </label>
    <button type="submit">Store on dummy server</button>
  </form>
  <form method="post" action="/session/{$safe}/verify">
    <button type="submit">Mark verified</button>
  </form>
  <form method="post" action="/session/{$safe}/reject">
    <button type="submit">Mark rejected</button>
  </form>
</body>
</html>
HTML;
    }
}
