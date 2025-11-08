import { http, HttpResponse } from 'msw';

const mockCoordinates = {
    coordinates: {
        x: Array.from({ length: 50 }, () => Math.random() * 100),
        y: Array.from({ length: 50 }, () => Math.random() * 100)
    }
};

let mockDatabaseLoaded = true;
let mockDatabaseName = "mock_database";
let mockColumns = ['x', 'y', 'label', 'value'];
let mockDataPreview = Array.from({ length: 10 }, (_, i) => ({
    _id: i + 1,
    x: Math.random() * 100,
    y: Math.random() * 100,
    label: `Label_${i}`,
    value: Math.random() * 50
}));
let mockTotalDocuments = 50;
let mockEmbeddingCompletedCount = 20;
let mockEmbeddingField = "value_embedding";
let mockMapVectors = mockCoordinates.coordinates;
let mockDatabases = [
    { name: "db1.db", tables: { data: { columns: mockColumns, row_count: 50 } } },
    { name: "db2.db", tables: { data: { columns: mockColumns, row_count: 30 } } }
];

export const handlers = [
    http.get('/api/visualise/get-coordinates', () => HttpResponse.json(mockCoordinates)),
    http.get('/api/database/columns', () => HttpResponse.json(mockColumns)),
    http.post('/api/visualise/get-point', async ({ request }) => {
        const { id } = await request.json();
        return HttpResponse.json({
            id,
            name: `Mock Point ${id}`,
            features: {
                score: Math.random(),
                category: ['A', 'B', 'C'][Math.floor(Math.random() * 3)],
            },
        });
    }),
    http.post('/api/visualise/get-column-values', async ({ request }) => {
        const { column } = await request.json();
        const values = {};
        for (let i = 0; i < 50; i++) values[i + 1] = `${column}_${i}`;
        return HttpResponse.json(values);
    }),
    http.get('/api/database/health', () => HttpResponse.json({ loaded: mockDatabaseLoaded, name: mockDatabaseName })),
    http.get('/api/visualise/list-databases', () => HttpResponse.json({ databases: mockDatabases, selectedDatabase: mockDatabaseLoaded ? mockDatabaseName : null })),
    http.get('/api/embeddings/check-progress', () => HttpResponse.json({ completedDocuments: mockEmbeddingCompletedCount })),
    http.post('/api/embedding/queue-embeddings', () => HttpResponse.json({ status: "success" })),
    http.post('/api/dimension-reduction/run', () => HttpResponse.json({ status: "success" })),
    http.get('/api/dimension-reduction/check-progress', () => HttpResponse.json({ status: "success", mapVectors: mockMapVectors })),
    http.post('/api/dimension-reduction/configure', () => HttpResponse.json({ status: "success" })),
    http.post('/api/embeddings/configure', async ({ request }) => {
        const data = await request.json();
        if (!data.embeddingModel) return HttpResponse.json({ status: "pending", message: "model downloading", logs: "" });
        return HttpResponse.json({ status: "success", message: "model loaded" });
    }),
    http.get('/api/embeddings/check-download', () => HttpResponse.json({ model: "mock_model", modelObject: "Object()", logs: "" })),
    http.get('/api/database/preview', () => HttpResponse.json(mockDataPreview)),
    http.get('/api/database/total-documents', () => HttpResponse.json({ totalDocuments: mockTotalDocuments })),
    http.post('/api/database/select-database', async ({ request }) => {
        const { database } = await request.json();
        mockDatabaseName = database;
        mockDatabaseLoaded = true;
        return HttpResponse.json({ status: "success" });
    }),
    http.post('/api/database/upload-file', async ({ request }) => HttpResponse.json({ status: "success" })),
    http.post('/api/visualise/simple-query', async ({ request }) => {
        const { field, query, operator } = await request.json();
        return HttpResponse.json([1, 2, 3, 4]);
    }),
    http.post('/api/visualise/sequential-query', async ({ request }) => {
        const { field, buckets } = await request.json();
        return HttpResponse.json(Array.from({ length: buckets }, (_, i) => [i + 1, i + 2, i + 3]));
    }),
    http.post('/api/visualise/categorical-query', async ({ request }) => {
        const { field, buckets } = await request.json();
        return HttpResponse.json(Array.from({ length: buckets }, () => [1, 2, 3]));
    }),
    http.get('/shutdown', () => HttpResponse.json({ message: "Server shutting down" })),
];
