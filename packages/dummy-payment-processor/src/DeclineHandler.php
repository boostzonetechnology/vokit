<?php

declare(strict_types=1);

namespace Vokit\DummyPayment;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final class DeclineHandler
{
    public function __construct(private readonly WebhookClient $webhooks)
    {
    }

    public function __invoke(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        $body = (array) $request->getParsedBody();
        $payload = [
            'event_id' => 'evt_sandbox_fail_' . bin2hex(random_bytes(8)),
            'invoice_id' => (string) ($body['invoice_id'] ?? ''),
            'amount_minor' => (int) ($body['amount_minor'] ?? 0),
            'currency' => strtoupper((string) ($body['currency'] ?? 'USD')),
            'status' => 'failed',
        ];
        try {
            $this->webhooks->post($payload);
        } catch (\Throwable $exc) {
            $response->getBody()->write('Payment webhook failed: ' . htmlspecialchars($exc->getMessage(), ENT_QUOTES, 'UTF-8'));
            return $response->withStatus(502)->withHeader('Content-Type', 'text/plain; charset=utf-8');
        }
        $response->getBody()->write('Payment marked failed. Vokit will not settle the invoice.');
        return $response->withHeader('Content-Type', 'text/plain; charset=utf-8');
    }
}
