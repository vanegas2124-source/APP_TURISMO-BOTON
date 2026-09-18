class MlTourismRequest {
  const MlTourismRequest({
    required this.usuarioId,
    required this.edad,
    required this.compania,
    required this.condicionFisica,
    required this.discapacidadFisica,
    required this.enfermedad,
    required this.actividadesPreferidas,
    required this.gustoNaturaleza,
    required this.gustoAventura,
    required this.importanciaSeguridad,
    required this.distancia,
    required this.duracion,
    required this.presupuesto,
    required this.aceptaLluvia,
    required this.climaPreferido,
    required this.riesgoAceptado,
    required this.riesgosPreocupantes,
    required this.latitud,
    required this.longitud,
  });

  final String? usuarioId;

  final String edad;
  final List<String> compania;
  final String condicionFisica;
  final String discapacidadFisica;
  final String enfermedad;

  final List<String> actividadesPreferidas;
  final String gustoNaturaleza;
  final String gustoAventura;
  final String importanciaSeguridad;

  final double distancia;
  final String duracion;
  final String presupuesto;

  final String aceptaLluvia;
  final String climaPreferido;

  final String riesgoAceptado;
  final List<String> riesgosPreocupantes;

  final double latitud;
  final double longitud;

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'perfil_usuario': <String, dynamic>{
        'usuario_id': usuarioId,
        'edad': edad,
        'compania': compania,
        'condicion_fisica': condicionFisica,
        'discapacidad_fisica': discapacidadFisica,
        'enfermedad': enfermedad,
      },

      'preferencias_actuales': <String, dynamic>{
        'actividades_preferidas': actividadesPreferidas,
        'gusto_naturaleza': gustoNaturaleza,
        'gusto_aventura': gustoAventura,
        'importancia_seguridad': importanciaSeguridad,
        'distancia': distancia,
        'duracion': duracion,
        'presupuesto': presupuesto,
        'acepta_lluvia': aceptaLluvia,
        'clima_preferido': climaPreferido,
        'riesgo_aceptado': riesgoAceptado,
        'riesgos_preocupantes': riesgosPreocupantes,
      },

      'ubicacion_actual': <String, dynamic>{
        'latitud': latitud,
        'longitud': longitud,
      },
    };
  }
}