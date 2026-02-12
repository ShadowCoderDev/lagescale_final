import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ─── Custom Metrics ──────────────────────────────────────────────
const errorRate = new Rate('errors');
const paymentDuration = new Trend('payment_duration', true);
const healthDuration = new Trend('health_check_duration', true);
const requestCount = new Counter('total_requests');

// ─── Test Configuration ─────────────────────────────────────────
export const options = {
    stages: [
        // Ramp-up
        { duration: '30s', target: 10 },   // 10 VU in 30s
        // Sustained load
        { duration: '1m', target: 20 },    // 20 VU for 1 min
        // Spike test
        { duration: '15s', target: 50 },   // Spike to 50 VU
        // Recovery
        { duration: '30s', target: 10 },   // Back to 10 VU
        // Ramp-down
        { duration: '15s', target: 0 },    // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'],     // 95% of requests under 2s
        http_req_failed: ['rate<0.1'],         // Error rate under 10%
        errors: ['rate<0.1'],
        health_check_duration: ['p(99)<500'],  // Health checks under 500ms
        payment_duration: ['p(95)<3000'],      // Payment processing under 3s
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost';

// ─── Helper Functions ────────────────────────────────────────────
function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

// ─── Main Test Function ──────────────────────────────────────────
export default function () {

    // ═══════ Health Checks ═══════
    group('Health Checks', function () {
        const services = [
            { name: 'user-service', port: 8001 },
            { name: 'product-service', port: 8002 },
            { name: 'order-service', port: 8003 },
            { name: 'payment-service', port: 8004 },
            { name: 'notification-service', port: 8005 },
        ];

        for (const svc of services) {
            const res = http.get(`${BASE_URL}:${svc.port}/health`);
            healthDuration.add(res.timings.duration);
            requestCount.add(1);

            const passed = check(res, {
                [`${svc.name} is healthy`]: (r) => r.status === 200,
                [`${svc.name} responds quickly`]: (r) => r.timings.duration < 500,
            });
            errorRate.add(!passed);
        }
    });

    sleep(0.5);

    // ═══════ Payment Service Load Test ═══════
    group('Payment Processing', function () {
        const orderId = randomInt(1000, 99999);

        // Test successful payment (.00 amounts)
        const successPayload = JSON.stringify({
            order_id: orderId,
            user_id: randomInt(1, 100),
            amount: randomInt(10, 500) + 0.00,
        });

        const payRes = http.post(
            `${BASE_URL}:8004/api/payments/process/`,
            successPayload,
            { headers: { 'Content-Type': 'application/json' } }
        );

        paymentDuration.add(payRes.timings.duration);
        requestCount.add(1);

        const payPassed = check(payRes, {
            'payment returns 200': (r) => r.status === 200,
            'payment has transaction_id': (r) => {
                try { return JSON.parse(r.body).transaction_id !== undefined; }
                catch (e) { return false; }
            },
            'payment processed under 2s': (r) => r.timings.duration < 2000,
        });
        errorRate.add(!payPassed);

        // Retrieve payment
        if (payRes.status === 200) {
            try {
                const txnId = JSON.parse(payRes.body).transaction_id;
                const getRes = http.get(`${BASE_URL}:8004/api/payments/${txnId}/`);
                requestCount.add(1);
                check(getRes, {
                    'get payment returns 200': (r) => r.status === 200,
                });
            } catch (e) { /* skip */ }
        }
    });

    sleep(0.5);

    // ═══════ User Service Load Test ═══════
    group('User Registration & Login', function () {
        const uniqueId = `${Date.now()}-${randomInt(1, 99999)}`;

        // Register
        const regPayload = JSON.stringify({
            email: `loadtest-${uniqueId}@test.com`,
            password: 'TestPass123!',
            password2: 'TestPass123!',
            first_name: 'Load',
            last_name: 'Test',
        });

        const regRes = http.post(
            `${BASE_URL}:8001/api/users/register/`,
            regPayload,
            { headers: { 'Content-Type': 'application/json' } }
        );
        requestCount.add(1);

        check(regRes, {
            'registration returns 201': (r) => r.status === 201,
        });

        // Login
        const loginPayload = JSON.stringify({
            email: `loadtest-${uniqueId}@test.com`,
            password: 'TestPass123!',
        });

        const loginRes = http.post(
            `${BASE_URL}:8001/api/users/login/`,
            loginPayload,
            { headers: { 'Content-Type': 'application/json' } }
        );
        requestCount.add(1);

        const loginPassed = check(loginRes, {
            'login returns 200': (r) => r.status === 200,
            'login has tokens': (r) => {
                try { return JSON.parse(r.body).tokens !== undefined; }
                catch (e) { return false; }
            },
        });
        errorRate.add(!loginPassed);
    });

    sleep(0.5);

    // ═══════ Product Service Load Test ═══════
    group('Product Service', function () {
        const listRes = http.get(`${BASE_URL}:8002/api/products/`);
        requestCount.add(1);

        check(listRes, {
            'products list returns 200': (r) => r.status === 200,
            'products response under 1s': (r) => r.timings.duration < 1000,
        });
    });

    sleep(1);
}

// ─── Summary Report ──────────────────────────────────────────────
export function handleSummary(data) {
    const summary = {
        timestamp: new Date().toISOString(),
        total_requests: data.metrics.total_requests ? data.metrics.total_requests.values.count : 0,
        http_req_duration: {
            avg: data.metrics.http_req_duration.values.avg.toFixed(2) + 'ms',
            p95: data.metrics.http_req_duration.values['p(95)'].toFixed(2) + 'ms',
            max: data.metrics.http_req_duration.values.max.toFixed(2) + 'ms',
        },
        error_rate: data.metrics.errors ? (data.metrics.errors.values.rate * 100).toFixed(2) + '%' : '0%',
        http_reqs: data.metrics.http_reqs.values.count,
        vus_max: data.metrics.vus_max.values.value,
    };

    console.log('\n══════════════════════════════════════════════');
    console.log('  LOAD TEST SUMMARY');
    console.log('══════════════════════════════════════════════');
    console.log(`  Total Requests    : ${summary.total_requests}`);
    console.log(`  HTTP Requests     : ${summary.http_reqs}`);
    console.log(`  Max VUs           : ${summary.vus_max}`);
    console.log(`  Avg Duration      : ${summary.http_req_duration.avg}`);
    console.log(`  P95 Duration      : ${summary.http_req_duration.p95}`);
    console.log(`  Max Duration      : ${summary.http_req_duration.max}`);
    console.log(`  Error Rate        : ${summary.error_rate}`);
    console.log('══════════════════════════════════════════════\n');

    return {
        'loadtest-results.json': JSON.stringify(data, null, 2),
    };
}
