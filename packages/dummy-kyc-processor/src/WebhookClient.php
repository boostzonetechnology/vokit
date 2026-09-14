<?php

declare(strict_types=1);

namespace Vokit\DummyKyc;

final class WebhookClient
{
    public function __construct(private readonly Config $config)
    {
    }

    /**
     * @param array<string, mixed> $payload
     */
    public function post(array $payload): string
    {
        $raw = json_encode($payload, JSON_THROW_ON_ERROR);
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => implode("\r\n", [
                    'Content-Type: application/json',
                    'X-Vokit-Kyc-Signature: ' . Hmac::sign($this->config->webhookSecret, $raw),
                ]),
                'content' => $raw,
                'ignore_errors' => true,
                'timeout' => 10,
            ],
        ]);
        $response = file_get_contents($this->config->webhookUrl(), false, $context);
        if ($response === false) {
            throw new \RuntimeException('Vokit KYC webhook is unreachable.');
        }
        return $response;
    }
}
