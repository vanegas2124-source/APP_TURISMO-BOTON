import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

import '../models/ml_tourism_request.dart';

class MlTourismApiException implements Exception {
  MlTourismApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class MlTourismApiService {
  MlTourismApiService({http.Client? httpClient})
    : _httpClient = httpClient ?? http.Client();

  final http.Client _httpClient;

  // ==========================================================
  // CONSTRUIR URL
  // ==========================================================

  Uri _buildEndpoint(String path) {
    final String? baseUrl = dotenv.env['RECOMMENDATION_API_URL'];

    if (baseUrl == null || baseUrl.trim().isEmpty) {
      throw MlTourismApiException(
        'No se encontró RECOMMENDATION_API_URL '
        'en el archivo .env.',
      );
    }

    final String normalizedBaseUrl = baseUrl.endsWith('/')
        ? baseUrl
        : '$baseUrl/';

    return Uri.parse(
      normalizedBaseUrl,
    ).resolve(path.startsWith('/') ? path.substring(1) : path);
  }

  // ==========================================================
  // POST GENÉRICO
  // ==========================================================

  Future<Map<String, dynamic>> _post(
    String path,
    MlTourismRequest request,
  ) async {
    final Uri endpoint = _buildEndpoint(path);

    debugPrint('[ML Turismo] POST $endpoint');

    try {
      final http.Response response = await _httpClient
          .post(
            endpoint,
            headers: const <String, String>{
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(request.toJson()),
          )
          .timeout(const Duration(seconds: 45));

      debugPrint(
        '[ML Turismo] HTTP '
        '${response.statusCode}',
      );

      // ------------------------------------------------------
      // ERROR HTTP
      // ------------------------------------------------------

      if (response.statusCode < 200 || response.statusCode >= 300) {
        String mensaje =
            'Error del servidor ML '
            '(HTTP ${response.statusCode}).';

        try {
          final dynamic decoded = jsonDecode(response.body);

          if (decoded is Map && decoded['detail'] != null) {
            mensaje = decoded['detail'].toString();
          }
        } catch (_) {
          // Conserva mensaje genérico.
        }

        throw MlTourismApiException(mensaje);
      }

      // ------------------------------------------------------
      // DECODIFICAR JSON
      // ------------------------------------------------------

      final dynamic decoded = jsonDecode(response.body);

      if (decoded is! Map<String, dynamic>) {
        throw MlTourismApiException(
          'El servidor ML devolvió '
          'un formato inesperado.',
        );
      }

      return decoded;
    }
    // --------------------------------------------------------
    // TIMEOUT
    // --------------------------------------------------------
    on TimeoutException {
      throw MlTourismApiException(
        'El modelo tardó demasiado '
        'en responder.',
      );
    }
    // --------------------------------------------------------
    // ERROR DE RED
    // --------------------------------------------------------
    on http.ClientException catch (error) {
      debugPrint(
        '[ML Turismo] '
        'Error de conexión: $error',
      );

      throw MlTourismApiException(
        'No fue posible conectar con '
        'el servicio de Machine Learning.',
      );
    }
    // --------------------------------------------------------
    // JSON INVÁLIDO
    // --------------------------------------------------------
    on FormatException catch (error) {
      debugPrint(
        '[ML Turismo] '
        'JSON inválido: $error',
      );

      throw MlTourismApiException(
        'El servidor ML devolvió '
        'una respuesta inválida.',
      );
    }
    // --------------------------------------------------------
    // ERROR CONTROLADO
    // --------------------------------------------------------
    on MlTourismApiException {
      rethrow;
    }
    // --------------------------------------------------------
    // ERROR GENERAL
    // --------------------------------------------------------
    catch (error) {
      debugPrint(
        '[ML Turismo] '
        'Error inesperado: $error',
      );

      throw MlTourismApiException(
        'Ocurrió un error inesperado '
        'al consultar los modelos.',
      );
    }
  }

  // ==========================================================
  // MODELO DE RESTRICCIONES
  // ==========================================================

  Future<Map<String, dynamic>> obtenerRestricciones(MlTourismRequest request) {
    return _post('v1/ml/modelo-restricciones', request);
  }

  // ==========================================================
  // MODELO DE RECOMENDACIÓN
  // ==========================================================

  Future<Map<String, dynamic>> obtenerRecomendacion(MlTourismRequest request) {
    return _post('v1/ml/modelo-recomendacion', request);
  }

  // ==========================================================
  // MODELO FINAL
  // ==========================================================

  Future<Map<String, dynamic>> obtenerResultadoFinal(MlTourismRequest request) {
    return _post('v1/ml/recomendar', request);
  }

  // ==========================================================
  // EJECUTAR LOS 3 MODELOS
  // ==========================================================

  Future<MlTourismResponses> ejecutarTodos(MlTourismRequest request) async {
    final List<Map<String, dynamic>> resultados =
        await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
          obtenerRecomendacion(request),
          obtenerRestricciones(request),
          obtenerResultadoFinal(request),
        ]);

    return MlTourismResponses(
      recomendacion: resultados[0],
      restricciones: resultados[1],
      resultadoFinal: resultados[2],
    );
  }

  void dispose() {
    _httpClient.close();
  }
}

// ============================================================
// RESPUESTAS DE LOS TRES MODELOS
// ============================================================

class MlTourismResponses {
  const MlTourismResponses({
    required this.recomendacion,
    required this.restricciones,
    required this.resultadoFinal,
  });

  final Map<String, dynamic> recomendacion;

  final Map<String, dynamic> restricciones;

  final Map<String, dynamic> resultadoFinal;
}
