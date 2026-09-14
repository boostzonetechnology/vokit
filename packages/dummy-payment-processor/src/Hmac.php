<?php

declare(strict_types=1);

namespace Vokit\DummyPayment;

final class Hmac
{
    public static function sign(string $secret, string $rawBody): string
    {
        return 'sha256=' . hash_hmac('sha256', $rawBody, $secret);
    }
}
