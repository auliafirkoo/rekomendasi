<?php
// ============================================================
// api_bridge.php
// Jembatan antara PHP dan Python Flask API
// Dipanggil via AJAX dari halaman utama (index.php)
// ============================================================

require_once __DIR__ . '/config.php';
header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? $_POST['action'] ?? '';

/**
 * Kirim HTTP request ke Python Flask API menggunakan cURL.
 */
function call_python(string $endpoint, string $method = 'GET', array $body = []): array
{
    $url = PYTHON_API_URL . $endpoint;
    $ch  = curl_init($url);

    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 30,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json'],
    ]);

    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
    }

    $response  = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_err  = curl_error($ch);
    curl_close($ch);

    if ($curl_err) {
        return ['error' => 'Tidak dapat terhubung ke Python engine: ' . $curl_err, 'code' => 0];
    }

    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return ['error' => 'Respons tidak valid dari Python engine', 'code' => $http_code];
    }

    $data['_http_code'] = $http_code;
    return $data;
}

// ── Router ────────────────────────────────────────────────────
switch ($action) {

    // Ambil opsi dropdown dari Python engine
    case 'options':
        echo json_encode(call_python('/api/options'));
        break;

    // Hitung rekomendasi
    case 'recommend':
        $payload = [
            'jenis'   => trim($_POST['jenis']   ?? ''),
            'tanaman' => trim($_POST['tanaman'] ?? ''),
            'opt'     => trim($_POST['opt']     ?? ''),
            'fase'    => trim($_POST['fase']    ?? ''),
            'top_n'   => (int)($_POST['top_n']  ?? 5),
        ];
        echo json_encode(call_python('/api/recommend', 'POST', $payload));
        break;

    // Cek status engine
    case 'health':
        echo json_encode(call_python('/api/health'));
        break;

    // Reload engine setelah update data MySQL
    case 'reload':
        echo json_encode(call_python('/api/reload', 'POST'));
        break;

    default:
        http_response_code(400);
        echo json_encode(['error' => 'Action tidak dikenal']);
}
