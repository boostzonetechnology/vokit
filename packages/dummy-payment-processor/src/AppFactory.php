<?php

declare(strict_types=1);

namespace Vokit\DummyPayment;

use Slim\Factory\AppFactory as SlimAppFactory;
use Slim\App;

final class AppFactory
{
    public static function create(): App
    {
        $config = Config::fromEnv();
        $webhooks = new WebhookClient($config);
        $app = SlimAppFactory::create();
        $app->addErrorMiddleware(false, true, false);
        $app->get('/', new HealthHandler());
        $app->get('/health', new HealthHandler());
        $app->get('/checkout', new CheckoutHandler());
        $app->post('/pay', new CaptureHandler($webhooks));
        $app->post('/fail', new DeclineHandler($webhooks));
        return $app;
    }
}
