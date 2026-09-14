<?php

declare(strict_types=1);

namespace Vokit\DummyPayment;

final class Config
{
    public function __construct(
        public readonly string $vokitBaseUrl,
        public readonly string $webhookSecret,
    ) {
        if ($this->vokitBaseUrl === '' || $this->webhookSecret === '') {
            throw new \RuntimeException('VOKIT_BASE_URL and SANDBOX_WEBHOOK_SECRET are required.');
        }
    }

    public static function fromEnv(): self
    {
        return new self(
            rtrim(self::env('VOKIT_BASE_URL'), '/'),
            self::env('SANDBOX_WEBHOOK_SECRET'),
        );
    }

    private static function env(string $key): string
    {
        $value = $_ENV[$key] ?? $_SERVER[$key] ?? getenv($key);
        return is_string($value) ? trim($value) : '';
    }

    public function webhookUrl(): string
    {
        return $this->vokitBaseUrl . '/webhooks/sandbox/v1/';
    }
}
