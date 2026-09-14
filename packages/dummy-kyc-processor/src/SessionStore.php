<?php

declare(strict_types=1);

namespace Vokit\DummyKyc;

use Psr\Http\Message\UploadedFileInterface;

final class SessionStore
{
    public function __construct(private readonly string $storageDir)
    {
    }

    public function sessionDir(string $sessionId): string
    {
        $safe = preg_replace('/[^a-zA-Z0-9_-]/', '', $sessionId) ?? '';
        if ($safe === '') {
            throw new \InvalidArgumentException('session_id is invalid.');
        }
        $dir = $this->storageDir . DIRECTORY_SEPARATOR . $safe;
        if (!is_dir($dir) && !mkdir($dir, 0700, true) && !is_dir($dir)) {
            throw new \RuntimeException('Unable to create KYC storage.');
        }
        return $dir;
    }

    /**
     * @return list<string>
     */
    public function listFiles(string $sessionId): array
    {
        $dir = $this->sessionDir($sessionId);
        $names = [];
        foreach (scandir($dir) ?: [] as $name) {
            if ($name === '.' || $name === '..') {
                continue;
            }
            if (is_file($dir . DIRECTORY_SEPARATOR . $name)) {
                $names[] = $name;
            }
        }
        return $names;
    }

    public function storeUpload(string $sessionId, UploadedFileInterface $upload): void
    {
        $originalName = $upload->getClientFilename() ?: 'upload.bin';
        $base = preg_replace('/[^a-zA-Z0-9._-]/', '_', $originalName) ?: 'upload.bin';
        $upload->moveTo($this->sessionDir($sessionId) . DIRECTORY_SEPARATOR . $base);
    }
}
