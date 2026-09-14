<?php

declare(strict_types=1);

namespace Vokit\DummyKyc;

use Slim\App;
use Slim\Factory\AppFactory as SlimAppFactory;

final class AppFactory
{
    public static function create(): App
    {
        $config = Config::fromEnv();
        $webhooks = new WebhookClient($config);
        $store = new SessionStore($config->storageDir);
        $app = SlimAppFactory::create();
        $app->addErrorMiddleware(false, true, false);
        $app->get('/', new HealthHandler());
        $app->get('/health', new HealthHandler());
        $show = new SessionShowHandler($store);
        $app->get('/session/{session_id}', $show);
        $app->post('/session/{session_id}', $show);
        $app->post('/session/{session_id}/verify', new SessionDecisionHandler($webhooks, 'verified'));
        $app->post('/session/{session_id}/reject', new SessionDecisionHandler($webhooks, 'rejected'));
        return $app;
    }
}
