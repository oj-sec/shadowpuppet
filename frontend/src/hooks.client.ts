import { dev } from '$app/environment';

if (dev) {
    const { worker } = await import('./mocks/browser');
    worker.start({
        onUnhandledRequest: 'bypass',
    });
}
