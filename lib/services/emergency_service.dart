import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/emergency_contact.dart';
import 'location_service.dart';

class EmergencyService {
  EmergencyService._();

  static final EmergencyService instance = EmergencyService._();

  static const String smsChannel = 'sms';
  static const String whatsappChannel = 'whatsapp';

  static const String _trustedContactKey = 'trusted_emergency_contact';
  static const String _trustedContactChannelKey =
      'trusted_emergency_contact_channel';

  static const List<EmergencyContact> officialContacts = <EmergencyContact>[
    EmergencyContact(
      name: 'Policía Nacional',
      phone: '123',
      description: 'Emergencias de seguridad y atención inmediata',
      icon: Icons.local_police,
    ),
    EmergencyContact(
      name: 'Bomberos',
      phone: '119',
      description: 'Incendios, rescates y emergencias',
      icon: Icons.fire_truck,
    ),
    EmergencyContact(
      name: 'Cruz Roja',
      phone: '132',
      description: 'Atención humanitaria y primeros auxilios',
      icon: Icons.medical_services,
    ),
    EmergencyContact(
      name: 'Defensa Civil',
      phone: '144',
      description: 'Emergencias, rescate y gestión del riesgo',
      icon: Icons.health_and_safety,
    ),
  ];

  Future<String?> loadTrustedContact() async {
    final SharedPreferences preferences = await SharedPreferences.getInstance();
    final String? phone = preferences.getString(_trustedContactKey);
    if (phone == null || phone.trim().isEmpty) {
      return null;
    }
    return phone.trim();
  }

  Future<String> loadTrustedContactChannel() async {
    final SharedPreferences preferences = await SharedPreferences.getInstance();
    final String? channel = preferences.getString(_trustedContactChannelKey);
    if (channel == whatsappChannel) {
      return whatsappChannel;
    }
    return smsChannel;
  }

  Future<void> saveTrustedContact({
    required String phone,
    required String channel,
  }) async {
    final SharedPreferences preferences = await SharedPreferences.getInstance();
    await preferences.setString(_trustedContactKey, phone.trim());
    await preferences.setString(
      _trustedContactChannelKey,
      channel == whatsappChannel ? whatsappChannel : smsChannel,
    );
  }

  Future<Position> getCurrentPosition() async {
    final LocationService locationService = LocationService.instance;
    await locationService.refresh();

    final Position? position = locationService.state.position;
    if (position == null) {
      throw StateError(
        locationService.state.errorMessage ??
            'No fue posible obtener la ubicación actual.',
      );
    }

    return position;
  }

  String buildSosMessage(Position position) {
    final String latitude = position.latitude.toStringAsFixed(6);
    final String longitude = position.longitude.toStringAsFixed(6);
    final String mapsUrl =
        'https://www.google.com/maps/search/?api=1&query=$latitude,$longitude';

    return '🚨 ALERTA SOS - APP TURISMO RESPONSABLE\n\n'
        'Necesito ayuda. Esta es mi ubicación actual:\n'
        '📍 $latitude, $longitude\n'
        '🗺️ $mapsUrl\n\n'
        'Por favor comunícate conmigo o solicita apoyo de los organismos de emergencia.';
  }

  Future<void> call(String phone) async {
    final Uri uri = Uri(scheme: 'tel', path: phone);
    final bool launched = await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );
    if (!launched) {
      throw StateError('No fue posible abrir la aplicación de llamadas.');
    }
  }

  Future<void> sendSms({
    required String phone,
    required String message,
  }) async {
    final Uri uri = Uri(
      scheme: 'sms',
      path: phone,
      queryParameters: <String, String>{'body': message},
    );
    final bool launched = await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );
    if (!launched) {
      throw StateError('No fue posible abrir la aplicación de mensajes.');
    }
  }

  Future<void> sendWhatsApp({
    required String phone,
    required String message,
  }) async {
    final String whatsappPhone = _normalizeWhatsAppPhone(phone);
    if (whatsappPhone.length < 10) {
      throw StateError(
        'El número configurado no es válido para WhatsApp.',
      );
    }

    final Uri uri = Uri.https(
      'wa.me',
      '/$whatsappPhone',
      <String, String>{'text': message},
    );

    final bool launched = await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );
    if (!launched) {
      throw StateError(
        'No fue posible abrir WhatsApp. Verifica que esté instalado.',
      );
    }
  }

  Future<void> sendSosToTrustedContact({
    required String phone,
    required String message,
    required String channel,
  }) async {
    if (channel == whatsappChannel) {
      await sendWhatsApp(phone: phone, message: message);
      return;
    }

    await sendSms(phone: phone, message: message);
  }

  String _normalizeWhatsAppPhone(String phone) {
    String digits = phone.replaceAll(RegExp(r'[^0-9]'), '');

    // Facilita números móviles colombianos escritos como 3001234567.
    if (digits.length == 10 && digits.startsWith('3')) {
      digits = '57$digits';
    }

    return digits;
  }

  Future<void> openNearbyEmergencyServices(Position position) async {
    final String coordinates =
        '${position.latitude.toStringAsFixed(6)},${position.longitude.toStringAsFixed(6)}';
    final Uri uri = Uri.https(
      'www.google.com',
      '/maps/search/',
      <String, String>{
        'api': '1',
        'query': 'servicios de emergencia cerca de $coordinates',
      },
    );

    final bool launched = await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );
    if (!launched) {
      throw StateError('No fue posible abrir el mapa de servicios cercanos.');
    }
  }
}
