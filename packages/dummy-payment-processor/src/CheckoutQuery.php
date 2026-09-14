<?php

declare(strict_types=1);

namespace Vokit\DummyPayment;

final class CheckoutQuery
{
    public function __construct(
        public readonly string $invoiceId,
        public readonly string $amountMinor,
        public readonly string $currency,
        public readonly string $clientReference,
    ) {
    }

    /**
     * @param array<string, mixed> $query
     */
    public static function fromQuery(array $query): self
    {
        return new self(
            trim((string) ($query['invoice_id'] ?? '')),
            trim((string) ($query['amount_minor'] ?? '')),
            strtoupper(trim((string) ($query['currency'] ?? 'USD'))),
            trim((string) ($query['client_reference'] ?? '')),
        );
    }

    public function isComplete(): bool
    {
        return $this->invoiceId !== '' && $this->amountMinor !== '' && $this->currency !== '';
    }
}
