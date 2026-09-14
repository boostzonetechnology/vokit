<?php

declare(strict_types=1);

namespace Vokit\DummyKyc;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final class SessionDecisionHandler
{
    public function __construct(
        private readonly WebhookClient $webhooks,
        private readonly string $status,
    ) {
    }

    public function __invoke(
        ServerRequestInterface $request,
        ResponseInterface $response,
        array $args,
    ): ResponseInterface {
        $sessionId = (string) ($args['session_id'] ?? '');
        $payload = [
            'event_id' => 'evt_kyc_' . $this->status . '_' . bin2hex(random_bytes(8)),
            'session_id' => $sessionId,
            'inquiry_id' => 'kycinq_' . $sessionId,
            'status' => $this->status,
            'reason_code' => $this->status === 'verified' ? 'ok' : 'rejected',
            'external_note' => '',
        ];
        try {
            $this->webhooks->post($payload);
        } catch (\Throwable $exc) {
            $response->getBody()->write('KYC webhook failed: ' . htmlspecialchars($exc->getMessage(), ENT_QUOTES, 'UTF-8'));
            return $response->withStatus(502)->withHeader('Content-Type', 'text/plain; charset=utf-8');
        }
        $label = $this->status === 'verified' ? 'verified' : 'rejected';
        $response->getBody()->write('KYC marked ' . $label . '. Vokit will update status from the webhook. Agency Active is unchanged.');
        return $response->withHeader('Content-Type', 'text/plain; charset=utf-8');
    }
}
