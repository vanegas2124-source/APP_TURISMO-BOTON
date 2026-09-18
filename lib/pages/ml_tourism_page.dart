import 'package:flutter/material.dart';

import '../models/ml_tourism_request.dart';
import '../services/ml_tourism_api_service.dart';

class MlTourismPage extends StatefulWidget {
  const MlTourismPage({super.key});

  @override
  State<MlTourismPage> createState() => _MlTourismPageState();
}

class _MlTourismPageState extends State<MlTourismPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  final MlTourismApiService _apiService = MlTourismApiService();

  bool _cargando = false;

  MlTourismResponses? _resultados;

  // =========================================================
  // DATOS DEL PERFIL
  // =========================================================

  String _edad = '26-35';
  String _compania = 'Pareja';
  String _condicionFisica = 'Media';
  String _discapacidadFisica = 'No';
  String _enfermedad = 'Ninguna';

  // =========================================================
  // PREFERENCIAS
  // =========================================================

  String _gustoNaturaleza = 'mucho';
  String _gustoAventura = 'poco';
  String _importanciaSeguridad = 'alta';

  double _distancia = 20;

  String _duracion = '1 a 3 horas';

  String _presupuesto = r'$20.000 – $50.000';

  String _aceptaLluvia = 'No';

  String _climaPreferido = 'soleado';

  String _riesgoAceptado = 'bajo';

  // =========================================================
  // ACTIVIDADES
  // =========================================================

  final Set<String> _actividadesSeleccionadas = <String>{
    'fotografia de paisajes',
  };

  final Set<String> _riesgosSeleccionados = <String>{
    'Clima (lluvia, tormentas)',
  };

  // =========================================================
  // UBICACIÓN
  // Por ahora manual.
  // Luego la conectamos con el GPS de la app.
  // =========================================================

  final TextEditingController _latitudController = TextEditingController();

  final TextEditingController _longitudController = TextEditingController();

  // =========================================================
  // OPCIONES
  // =========================================================

  static const List<String> edades = <String>[
    'MENOR DE 18',
    '18-25',
    '26-35',
    '36-50',
    'MAYOR DE 50',
  ];

  static const List<String> companias = <String>[
    'Solo',
    'Pareja',
    'Amigos',
    'Familia',
    'Con niños',
    'Con adultos mayores',
  ];

  static const List<String> condicionesFisicas = <String>[
    'Baja',
    'Media',
    'Alta',
  ];

  static const List<String> enfermedades = <String>[
    'Ninguna',
    'Cardiaca',
    'Respiratoria',
    'Ambas',
  ];

  static const List<String> nivelesGusto = <String>[
    'nada',
    'poco',
    'moderado',
    'mucho',
  ];

  static const List<String> nivelesSeguridad = <String>[
    'baja',
    'media',
    'alta',
  ];

  static const List<String> duraciones = <String>[
    'menos de una hora',
    '1 a 3 horas',
    'medio dia',
    'todo el dia',
  ];

  static const List<String> presupuestos = <String>[
    'Menos de \$20.000',
    '\$20.000 – \$50.000',
    '\$50.000 – \$100.000',
    'Más de \$100.000',
  ];

  static const List<String> climas = <String>[
    'soleado',
    'nublado',
    'frio',
    'no importa',
  ];

  static const List<String> riesgosAceptados = <String>[
    'bajo',
    'medio',
    'alto',
  ];

  static const List<String> actividades = <String>[
    'Caminata ecologica',
    'fotografia de paisajes',
    'avistamiento de fauna',
    'relajacion y descanso',
    'aventura(senderismo ,escalar )',
    'actividades culturales',
  ];

  static const List<String> riesgos = <String>[
    'Clima (lluvia, tormentas)',
    'Terreno difícil (lodo, pendientes)',
    'Fauna peligrosa',
    'Perderse',
    'Accidentes',
  ];

  @override
  void dispose() {
    _latitudController.dispose();
    _longitudController.dispose();
    _apiService.dispose();

    super.dispose();
  }

  // =========================================================
  // EJECUTAR MODELOS
  // =========================================================

  Future<void> _analizarPerfil() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_actividadesSeleccionadas.isEmpty) {
      _mostrarMensaje('Selecciona al menos una actividad.');
      return;
    }

    final double? latitud = double.tryParse(_latitudController.text.trim());

    final double? longitud = double.tryParse(_longitudController.text.trim());

    if (latitud == null || longitud == null) {
      _mostrarMensaje('Debes ingresar una ubicación válida.');
      return;
    }

    final MlTourismRequest request = MlTourismRequest(
      usuarioId: null,
      edad: _edad,
      compania: <String>[_compania],
      condicionFisica: _condicionFisica,
      discapacidadFisica: _discapacidadFisica,
      enfermedad: _enfermedad,
      actividadesPreferidas: _actividadesSeleccionadas.toList(),
      gustoNaturaleza: _gustoNaturaleza,
      gustoAventura: _gustoAventura,
      importanciaSeguridad: _importanciaSeguridad,
      distancia: _distancia,
      duracion: _duracion,
      presupuesto: _presupuesto,
      aceptaLluvia: _aceptaLluvia,
      climaPreferido: _climaPreferido,
      riesgoAceptado: _riesgoAceptado,
      riesgosPreocupantes: _riesgosSeleccionados.toList(),
      latitud: latitud,
      longitud: longitud,
    );

    setState(() {
      _cargando = true;
      _resultados = null;
    });

    try {
      final MlTourismResponses respuesta = await _apiService.ejecutarTodos(
        request,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _resultados = respuesta;
      });
    } on MlTourismApiException catch (error) {
      if (!mounted) {
        return;
      }

      _mostrarMensaje(error.message);
    } catch (error) {
      if (!mounted) {
        return;
      }

      _mostrarMensaje('Error inesperado: $error');
    } finally {
      if (mounted) {
        setState(() {
          _cargando = false;
        });
      }
    }
  }

  void _mostrarMensaje(String mensaje) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(mensaje)));
  }

  // =========================================================
  // INTERFAZ
  // =========================================================

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: _resultados == null ? _buildFormulario() : _buildResultados(),
    );
  }

  Widget _buildFormulario() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          const Text(
            'Encuentra una experiencia para ti',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 8),

          const Text(
            'Completa tu perfil. Los modelos analizarán '
            'tus preferencias, restricciones y ubicación.',
          ),

          const SizedBox(height: 24),

          _tituloSeccion('1. Perfil del turista', Icons.person),

          _dropdown(
            label: 'Edad',
            value: _edad,
            values: edades,
            onChanged: (String value) {
              setState(() {
                _edad = value;
              });
            },
          ),

          _dropdown(
            label: '¿Con quién viajas?',
            value: _compania,
            values: companias,
            onChanged: (String value) {
              setState(() {
                _compania = value;
              });
            },
          ),

          _dropdown(
            label: 'Condición física',
            value: _condicionFisica,
            values: condicionesFisicas,
            onChanged: (String value) {
              setState(() {
                _condicionFisica = value;
              });
            },
          ),

          _dropdown(
            label: 'Discapacidad física',
            value: _discapacidadFisica,
            values: const <String>['No', 'Sí'],
            onChanged: (String value) {
              setState(() {
                _discapacidadFisica = value;
              });
            },
          ),

          _dropdown(
            label: 'Condición de salud',
            value: _enfermedad,
            values: enfermedades,
            onChanged: (String value) {
              setState(() {
                _enfermedad = value;
              });
            },
          ),

          const SizedBox(height: 24),

          _tituloSeccion('2. Actividades preferidas', Icons.hiking),

          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: actividades.map((String actividad) {
              final bool seleccionada = _actividadesSeleccionadas.contains(
                actividad,
              );

              return FilterChip(
                label: Text(actividad),
                selected: seleccionada,
                onSelected: (bool value) {
                  setState(() {
                    if (value) {
                      _actividadesSeleccionadas.add(actividad);
                    } else {
                      _actividadesSeleccionadas.remove(actividad);
                    }
                  });
                },
              );
            }).toList(),
          ),

          const SizedBox(height: 24),

          _tituloSeccion('3. Preferencias', Icons.tune),

          _dropdown(
            label: 'Gusto por la naturaleza',
            value: _gustoNaturaleza,
            values: nivelesGusto,
            onChanged: (String value) {
              setState(() {
                _gustoNaturaleza = value;
              });
            },
          ),

          _dropdown(
            label: 'Gusto por la aventura',
            value: _gustoAventura,
            values: nivelesGusto,
            onChanged: (String value) {
              setState(() {
                _gustoAventura = value;
              });
            },
          ),

          _dropdown(
            label: 'Importancia de la seguridad',
            value: _importanciaSeguridad,
            values: nivelesSeguridad,
            onChanged: (String value) {
              setState(() {
                _importanciaSeguridad = value;
              });
            },
          ),

          const SizedBox(height: 12),

          Text(
            'Distancia máxima: '
            '${_distancia.toStringAsFixed(0)} km',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),

          Slider(
            min: 5,
            max: 30,
            divisions: 5,
            value: _distancia,
            label: '${_distancia.round()} km',
            onChanged: (double value) {
              setState(() {
                _distancia = value;
              });
            },
          ),

          _dropdown(
            label: 'Duración preferida',
            value: _duracion,
            values: duraciones,
            onChanged: (String value) {
              setState(() {
                _duracion = value;
              });
            },
          ),

          _dropdown(
            label: 'Presupuesto',
            value: _presupuesto,
            values: presupuestos,
            onChanged: (String value) {
              setState(() {
                _presupuesto = value;
              });
            },
          ),

          _dropdown(
            label: '¿Aceptas lluvia?',
            value: _aceptaLluvia,
            values: const <String>['Sí', 'No'],
            onChanged: (String value) {
              setState(() {
                _aceptaLluvia = value;
              });
            },
          ),

          _dropdown(
            label: 'Clima preferido',
            value: _climaPreferido,
            values: climas,
            onChanged: (String value) {
              setState(() {
                _climaPreferido = value;
              });
            },
          ),

          _dropdown(
            label: 'Riesgo aceptado',
            value: _riesgoAceptado,
            values: riesgosAceptados,
            onChanged: (String value) {
              setState(() {
                _riesgoAceptado = value;
              });
            },
          ),

          const SizedBox(height: 20),

          const Text(
            '¿Qué riesgos te preocupan?',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),

          const SizedBox(height: 8),

          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: riesgos.map((String riesgo) {
              return FilterChip(
                label: Text(riesgo),
                selected: _riesgosSeleccionados.contains(riesgo),
                onSelected: (bool value) {
                  setState(() {
                    if (value) {
                      _riesgosSeleccionados.add(riesgo);
                    } else {
                      _riesgosSeleccionados.remove(riesgo);
                    }
                  });
                },
              );
            }).toList(),
          ),

          const SizedBox(height: 24),

          _tituloSeccion('4. Ubicación actual', Icons.location_on),

          const Text(
            'Por ahora ingresaremos las coordenadas '
            'manualmente. En el siguiente ajuste '
            'las tomaremos automáticamente del GPS.',
          ),

          const SizedBox(height: 12),

          TextFormField(
            controller: _latitudController,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: true,
            ),
            decoration: const InputDecoration(
              labelText: 'Latitud',
              border: OutlineInputBorder(),
            ),
            validator: _validarCoordenada,
          ),

          const SizedBox(height: 12),

          TextFormField(
            controller: _longitudController,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: true,
            ),
            decoration: const InputDecoration(
              labelText: 'Longitud',
              border: OutlineInputBorder(),
            ),
            validator: _validarCoordenada,
          ),

          const SizedBox(height: 28),

          FilledButton.icon(
            onPressed: _cargando ? null : _analizarPerfil,
            icon: _cargando
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.psychology_alt),
            label: Padding(
              padding: const EdgeInsets.symmetric(vertical: 14),
              child: Text(_cargando ? 'Analizando...' : 'Analizar mi perfil'),
            ),
          ),

          const SizedBox(height: 30),
        ],
      ),
    );
  }

  // =========================================================
  // RESULTADOS
  // =========================================================

  Widget _buildResultados() {
    final MlTourismResponses resultados = _resultados!;

    return DefaultTabController(
      length: 3,
      child: Column(
        children: <Widget>[
          Material(
            elevation: 1,
            child: TabBar(
              isScrollable: true,
              tabs: const <Widget>[
                Tab(icon: Icon(Icons.favorite_outline), text: 'Recomendación'),
                Tab(icon: Icon(Icons.health_and_safety), text: 'Restricciones'),
                Tab(icon: Icon(Icons.auto_awesome), text: 'Resultado final'),
              ],
            ),
          ),

          Expanded(
            child: TabBarView(
              children: <Widget>[
                _recomendacionTab(resultados.recomendacion),
                _restriccionesTab(resultados.restricciones),
                _resultadoFinalTab(resultados.resultadoFinal),
              ],
            ),
          ),

          Padding(
            padding: const EdgeInsets.all(12),
            child: OutlinedButton.icon(
              onPressed: () {
                setState(() {
                  _resultados = null;
                });
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Realizar otro análisis'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _recomendacionTab(Map<String, dynamic> resultado) {
    final List<dynamic> top =
        resultado['top_3'] as List<dynamic>? ?? <dynamic>[];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        const Text(
          'Modelo de recomendación',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),

        const SizedBox(height: 8),

        const Text(
          'Estos lugares corresponden mejor '
          'con tus preferencias.',
        ),

        const SizedBox(height: 18),

        ...top.map(
          (dynamic item) => _tarjetaLugar(
            item as Map<String, dynamic>,
            tipo: 'recomendacion',
          ),
        ),
      ],
    );
  }

  Widget _restriccionesTab(Map<String, dynamic> resultado) {
    final List<dynamic> aptos =
        resultado['top_lugares_aptos'] as List<dynamic>? ?? <dynamic>[];

    final List<dynamic> descartados =
        resultado['lugares_descartados_por_restricciones'] as List<dynamic>? ??
        <dynamic>[];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        const Text(
          'Modelo de restricciones',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),

        const SizedBox(height: 16),

        Text(
          'Lugares aptos: ${aptos.length}',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),

        const SizedBox(height: 10),

        ...aptos.map(
          (dynamic item) =>
              _tarjetaLugar(item as Map<String, dynamic>, tipo: 'restriccion'),
        ),

        if (descartados.isNotEmpty) ...<Widget>[
          const SizedBox(height: 20),

          const Divider(),

          const Text(
            'Lugares descartados',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 10),

          ...descartados.map((dynamic value) {
            final Map<String, dynamic> item = value as Map<String, dynamic>;

            final List<dynamic> razones =
                item['razones_bloqueo'] as List<dynamic>? ?? <dynamic>[];

            return Card(
              child: ListTile(
                leading: const Icon(Icons.block),
                title: Text(item['lugar']?.toString() ?? 'Lugar'),
                subtitle: Text(
                  razones.map((dynamic e) => '• ${e.toString()}').join('\n'),
                ),
              ),
            );
          }),
        ],
      ],
    );
  }

  Widget _resultadoFinalTab(Map<String, dynamic> resultado) {
    final Map<String, dynamic> finalData =
        resultado['resultado_final'] as Map<String, dynamic>? ??
        <String, dynamic>{};

    final List<dynamic> top =
        finalData['top_3'] as List<dynamic>? ?? <dynamic>[];

    final String? recomendado = finalData['lugar_recomendado']?.toString();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: <Widget>[
        const Text(
          'Resultado final',
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),

        const SizedBox(height: 8),

        Text(resultado['mensaje']?.toString() ?? ''),

        if (recomendado != null) ...<Widget>[
          const SizedBox(height: 18),

          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: <Widget>[
                  const Icon(Icons.emoji_events, size: 42),

                  const SizedBox(height: 8),

                  const Text(
                    'Mejor opción para ti',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),

                  const SizedBox(height: 8),

                  Text(
                    recomendado,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 21,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],

        const SizedBox(height: 18),

        ...top.map(
          (dynamic item) =>
              _tarjetaLugar(item as Map<String, dynamic>, tipo: 'final'),
        ),

        if (top.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(18),
              child: Text(
                'No se encontraron lugares '
                'compatibles con todas las '
                'restricciones.',
              ),
            ),
          ),
      ],
    );
  }

  // =========================================================
  // TARJETA DE LUGAR
  // =========================================================

  Widget _tarjetaLugar(Map<String, dynamic> item, {required String tipo}) {
    final String lugar = item['lugar']?.toString() ?? 'Lugar turístico';

    final dynamic distancia = item['distancia_km'];

    final dynamic probabilidad =
        item['probabilidad'] ??
        item['probabilidad_apto'] ??
        item['probabilidad_recomendacion'];

    final dynamic puntaje = item['puntaje_final'];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              lugar,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            if (probabilidad != null)
              Text(
                'Probabilidad: '
                '${(double.tryParse(probabilidad.toString()) ?? 0) * 100}'
                '%',
              ),

            if (puntaje != null) Text('Puntaje final: $puntaje'),

            if (distancia != null) Text('Distancia: $distancia km'),

            if (item['nivel_riesgo_lugar'] != null)
              Text(
                'Riesgo: '
                '${item['nivel_riesgo_lugar']}',
              ),

            if (item['nivel_esfuerzo_lugar'] != null)
              Text(
                'Esfuerzo: '
                '${item['nivel_esfuerzo_lugar']}',
              ),
          ],
        ),
      ),
    );
  }

  // =========================================================
  // COMPONENTES
  // =========================================================

  Widget _tituloSeccion(String titulo, IconData icono) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: <Widget>[
          Icon(icono),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              titulo,
              style: const TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _dropdown({
    required String label,
    required String value,
    required List<String> values,
    required ValueChanged<String> onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<String>(
        initialValue: value,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
        ),
        items: values
            .map(
              (String value) =>
                  DropdownMenuItem<String>(value: value, child: Text(value)),
            )
            .toList(),
        onChanged: (String? value) {
          if (value != null) {
            onChanged(value);
          }
        },
      ),
    );
  }

  String? _validarCoordenada(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Campo obligatorio';
    }

    if (double.tryParse(value.trim()) == null) {
      return 'Ingresa un número válido';
    }

    return null;
  }
}
