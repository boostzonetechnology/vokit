<?php

declare(strict_types=1);

namespace Vokit\DummyPayment;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final class CheckoutHandler
{
    public function __invoke(ServerRequestInterface $request, ResponseInterface $response): ResponseInterface
    {
        $checkout = CheckoutQuery::fromQuery($request->getQueryParams());
        $html = self::page($checkout);
        $response->getBody()->write($html);
        return $response->withHeader('Content-Type', 'text/html; charset=utf-8');
    }

    private static function page(CheckoutQuery $checkout): string
    {
        $invoice = htmlspecialchars($checkout->invoiceId, ENT_QUOTES, 'UTF-8');
        $amount = htmlspecialchars($checkout->amountMinor, ENT_QUOTES, 'UTF-8');
        $currency = htmlspecialchars($checkout->currency, ENT_QUOTES, 'UTF-8');
        $reference = htmlspecialchars($checkout->clientReference, ENT_QUOTES, 'UTF-8');
        $disabled = $checkout->isComplete() ? '' : 'disabled';
        $warning = $checkout->isComplete()
            ? ''
            : '<p>Missing invoice fields from Vokit. Go back and pay from the customer portal.</p>';
        return <<<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Vokit lab payment</title>
</head>
<body>
  <h1>Dummy payment processor</h1>
  <p>Lab host only. Cards are not collected. Vokit settles after a signed webhook.</p>
  {$warning}
  <p>Invoice: {$invoice}</p>
  <p>Amount (minor units): {$amount} {$currency}</p>
  <p>Reference: {$reference}</p>
  <form method="post" action="/pay">
    <input type="hidden" name="invoice_id" value="{$invoice}">
    <input type="hidden" name="amount_minor" value="{$amount}">
    <input type="hidden" name="currency" value="{$currency}">
    <input type="hidden" name="client_reference" value="{$reference}">
    <button type="submit" {$disabled}>Mark paid</button>
  </form>
  <form method="post" action="/fail">
    <input type="hidden" name="invoice_id" value="{$invoice}">
    <input type="hidden" name="amount_minor" value="{$amount}">
    <input type="hidden" name="currency" value="{$currency}">
    <input type="hidden" name="client_reference" value="{$reference}">
    <button type="submit" {$disabled}>Mark failed</button>
  </form>
</body>
</html>
HTML;
    }
}
