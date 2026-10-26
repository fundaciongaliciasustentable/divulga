<?php
/*
 * Votación «Críaste este mito?» de v/habelos-hainos/.
 *
 * GET  → {"totais": {"<mito>": {"si": n, "non": n}, ...}, "persoas": n}
 * POST {"votante": "<id aleatorio do navegador>", "mito": "<id>", "voto": "si"|"non"}
 *      → os mesmos totais, xa co voto contado.
 *
 * Un voto por navegador e mito (cambiar o voto substitúe o anterior). O
 * identificador do navegador e a IP gárdanse só como hash. Os datos viven en
 * api/datos/, que non se serve (.htaccess) e que non vai no paquete de dist/:
 * ao volver subir o sitio non se perden os votos.
 * Compatible con PHP 7.4 ou superior.
 */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

// Deben coincidir cos IDS de v/habelos-hainos/index.html
const MITOS = ['chove', 'seca', 'quecemento', 'piromanos', 'monte-publico', 'eucalipto', 'proteccion', 'pampa',
               'renovable', 'solar', 'electrico', 'acuicultura', 'leite', 'local', 'migracion', 'minifundio', 'lobo'];
const VOTOS = ['si', 'non'];
const DIR_DATOS = __DIR__ . '/datos';
const FICHEIRO = DIR_DATOS . '/.ht-votos-habelos.json';
const MAX_VOTANTES = 200000;
const MAX_ESCRITURAS_HORA_IP = 120;

function responder(int $codigo, array $corpo): void
{
    http_response_code($codigo);
    echo json_encode($corpo, JSON_UNESCAPED_UNICODE);
    exit;
}

function totais(array $d): array
{
    $t = [];
    foreach (MITOS as $m) {
        $t[$m] = ['si' => 0, 'non' => 0];
    }
    foreach ($d['votantes'] as $votos) {
        foreach ($votos as $m => $v) {
            if (isset($t[$m][$v])) {
                $t[$m][$v]++;
            }
        }
    }
    return ['totais' => $t, 'persoas' => count($d['votantes'])];
}

$metodo = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($metodo !== 'GET' && $metodo !== 'POST') {
    header('Allow: GET, POST');
    responder(405, ['erro' => 'metodo']);
}

if (!is_dir(DIR_DATOS) && !@mkdir(DIR_DATOS, 0750)) {
    responder(503, ['erro' => 'almacenamento']);
}
$fp = @fopen(FICHEIRO, 'c+');
if (!$fp || !flock($fp, $metodo === 'POST' ? LOCK_EX : LOCK_SH)) {
    responder(503, ['erro' => 'almacenamento']);
}
$bruto = stream_get_contents($fp);
$d = $bruto ? json_decode($bruto, true) : null;
if (!is_array($d) || !isset($d['votantes']) || !is_array($d['votantes'])) {
    $d = ['votantes' => [], 'ips' => ['hora' => '', 'n' => []]];
}

if ($metodo === 'GET') {
    responder(200, totais($d));
}

$entrada = json_decode((string) file_get_contents('php://input', false, null, 0, 2048), true);
$votante = is_array($entrada) ? ($entrada['votante'] ?? '') : '';
$mito = is_array($entrada) ? ($entrada['mito'] ?? '') : '';
$voto = is_array($entrada) ? ($entrada['voto'] ?? '') : '';
if (!is_string($votante) || !preg_match('/^[A-Za-z0-9-]{16,64}$/', $votante)
    || !in_array($mito, MITOS, true) || !in_array($voto, VOTOS, true)) {
    responder(400, ['erro' => 'datos']);
}

// Límite de escrituras por IP e hora; a IP só se garda como hash e bórrase cada hora
$hora = gmdate('YmdH');
if (($d['ips']['hora'] ?? '') !== $hora) {
    $d['ips'] = ['hora' => $hora, 'n' => []];
}
$ip = hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '') . '|' . $hora);
$d['ips']['n'][$ip] = ($d['ips']['n'][$ip] ?? 0) + 1;
if ($d['ips']['n'][$ip] > MAX_ESCRITURAS_HORA_IP) {
    responder(429, ['erro' => 'limite']);
}

$clave = hash('sha256', $votante);
if (!isset($d['votantes'][$clave]) && count($d['votantes']) >= MAX_VOTANTES) {
    responder(503, ['erro' => 'cheo']);
}
$d['votantes'][$clave][$mito] = $voto;

ftruncate($fp, 0);
rewind($fp);
fwrite($fp, json_encode($d));
fflush($fp);
flock($fp, LOCK_UN);
fclose($fp);

responder(200, totais($d));
