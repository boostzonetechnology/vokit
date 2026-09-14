<?php

declare(strict_types=1);

namespace Vokit\DummyKyc;

final class Config
{
    public function __construct(
        public readonly string $vokitBaseUrl,
        public readonly string $webhookSecret,
        public readonly string $storageDir,
    ) {
        if ($this->vokitBaseUrl === '' || $this->webhookSecret === '') {
            throw new \RuntimeException('VOKIT_BASE_URL and KYC_WEBHOOK_SECRET are required.');
        }
    }

    public static function fromEnv(): self
    {
        $root = dirname(__DIR__);
        return new self(
            self::env('VOKIT_BASE_URL'),
            self::env('KYC_WEBHOOK_SECRET'),
            $root . DIRECTORY_SEPARATOR . 'storage',
        );
    }

    public function webhookUrl(): string
    {
        return rtrim($this->vokitBaseUrl, '/') . '/webhooks/kyc/external/v1/';
    }

    private static function env(string $key): string
    {
        $value = $_ENV[$key] ?? $_SERVER[$key] ?? getenv($key);
        return is_string($value) ? trim($value) : '';
    }
}
