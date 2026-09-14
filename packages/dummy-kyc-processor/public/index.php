<?php

declare(strict_types=1);

use Vokit\DummyKyc\AppFactory;

require dirname(__DIR__) . '/vendor/autoload.php';

$root = dirname(__DIR__);
if (is_file($root . '/.env')) {
    $dotenv = Dotenv\Dotenv::createImmutable($root);
    $dotenv->safeLoad();
}

$app = AppFactory::create();
$app->run();
