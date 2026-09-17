import 'dart:async';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../models/emergency_contact.dart';
import '../services/emergency_service.dart';
import '../services/location_service.dart';

class SecurityPage extends StatefulWidget {
  const SecurityPage({super.key});

  @override
  State<SecurityPage> createState() => _SecurityPageState();
}

class _SecurityPageState extends State<SecurityPage> {
  final EmergencyService _emergencyService = EmergencyService.instance;
  final LocationService _locationService = LocationService.instance;
  final TextEditingController _trustedContactController =
      TextEditingController();

  String? _trustedContact;
  String _trustedContactChannel = EmergencyService.smsChannel;
  bool _isSendingSos = false;
  bool _isOpeningNearbyHelp = false;

  @override
  void initState() {
    super.initState();
    unawaited(_loadTrustedContact());
    if (_locationService.state.position == null) {
      unawaited(_locationService.initialize());
    }
  }

  @override
  void dispose() {
    _trustedContactController.dispose();
    super.dispose();
  }

  Future<void> _loadTrustedContact() async {
    final String? phone = await _emergencyService.loadTrustedContact();
    final String channel =
        await _emergencyService.loadTrustedContactChannel();
    if (!mounted) {
      return;
    }
    setState(() {
      _trustedContact = phone;
      _trustedContactChannel = channel;
      _trustedContactController.text = phone ?? '';
    });
  }

  Future<void> _configureTrustedContact() async {
    _trustedContactController.text = _trustedContact ?? '';
    String selectedChannel = _trustedContactChannel;

    final bool? saved = await showDialog<bool>(
      context: context,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          title: const Text('Contacto de confianza'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text(
                'Este número recibirá el mensaje SOS con tu ubicación.',
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _trustedContactController,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Número de celular',
                  hintText: 'Ej. 3001234567',
                  prefixIcon: Icon(Icons.phone_android),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              StatefulBuilder(
                builder: (BuildContext context, StateSetter setDialogState) {
                  return Column(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      DropdownButtonFormField<String>(
                        value: selectedChannel,
                        decoration: const InputDecoration(
                          labelText: 'Enviar SOS por',
                          prefixIcon: Icon(Icons.send),
                          border: OutlineInputBorder(),
                        ),
                        items: const <DropdownMenuItem<String>>[
                          DropdownMenuItem<String>(
                            value: EmergencyService.smsChannel,
                            child: Text('SMS'),
                          ),
                          DropdownMenuItem<String>(
                            value: EmergencyService.whatsappChannel,
                            child: Text('WhatsApp'),
                          ),
                        ],
                        onChanged: (String? value) {
                          if (value == null) {
                            return;
                          }
                          setDialogState(() {
                            selectedChannel = value;
                          });
                        },
                      ),
                      if (selectedChannel ==
                          EmergencyService.whatsappChannel) ...<Widget>[
                        const SizedBox(height: 10),
                        const Text(
                          'Para WhatsApp se usará el formato internacional. Si escribes un celular colombiano de 10 dígitos, la app agregará +57 automáticamente.',
                          style: TextStyle(fontSize: 12),
                        ),
                      ],
                    ],
                  );
                },
              ),
            ],
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () async {
                final String phone = _trustedContactController.text
                    .replaceAll(RegExp(r'[^0-9+]'), '')
                    .trim();
                if (phone.length < 7) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Ingresa un número de teléfono válido.'),
                    ),
                  );
                  return;
                }

                await _emergencyService.saveTrustedContact(
                  phone: phone,
                  channel: selectedChannel,
                );
                if (dialogContext.mounted) {
                  Navigator.of(dialogContext).pop(true);
                }
              },
              child: const Text('Guardar'),
            ),
          ],
        );
      },
    );

    if (saved == true) {
      await _loadTrustedContact();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Contacto de confianza guardado.')),
      );
    }
  }

  Future<void> _sendSos() async {
    if (_isSendingSos) {
      return;
    }

    final String? trustedContact = _trustedContact;
    if (trustedContact == null || trustedContact.isEmpty) {
      await _configureTrustedContact();
      return;
    }

    setState(() {
      _isSendingSos = true;
    });

    try {
      final Position position = await _emergencyService.getCurrentPosition();
      final String message = _emergencyService.buildSosMessage(position);
      await _emergencyService.sendSosToTrustedContact(
        phone: trustedContact,
        message: message,
        channel: _trustedContactChannel,
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$error')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSendingSos = false;
        });
      }
    }
  }

  Future<void> _callEmergency(EmergencyContact contact) async {
    try {
      await _emergencyService.call(contact.phone);
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$error')),
      );
    }
  }

  Future<void> _openNearbyHelp() async {
    if (_isOpeningNearbyHelp) {
      return;
    }

    setState(() {
      _isOpeningNearbyHelp = true;
    });

    try {
      final Position position = await _emergencyService.getCurrentPosition();
      await _emergencyService.openNearbyEmergencyServices(position);
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$error')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isOpeningNearbyHelp = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;

    return RefreshIndicator(
      onRefresh: _locationService.refresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          Card(
            elevation: 0,
            color: colors.errorContainer,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: <Widget>[
                  Icon(
                    Icons.sos,
                    size: 54,
                    color: colors.onErrorContainer,
                  ),
                  const SizedBox(height: 10),
                  Text(
                    '¿Necesitas ayuda?',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: colors.onErrorContainer,
                        ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Mantén presionado el botón SOS para preparar un mensaje con tu ubicación.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: colors.onErrorContainer),
                  ),
                  const SizedBox(height: 18),
                  Semantics(
                    button: true,
                    label: 'Botón SOS. Mantener presionado para pedir ayuda.',
                    child: GestureDetector(
                      onLongPress: _isSendingSos ? null : _sendSos,
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        width: 150,
                        height: 150,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: colors.error,
                          boxShadow: <BoxShadow>[
                            BoxShadow(
                              blurRadius: 16,
                              spreadRadius: 2,
                              color: colors.error.withValues(alpha: 0.35),
                            ),
                          ],
                        ),
                        alignment: Alignment.center,
                        child: _isSendingSos
                            ? CircularProgressIndicator(
                                color: colors.onError,
                              )
                            : Text(
                                'SOS',
                                style: TextStyle(
                                  color: colors.onError,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 36,
                                ),
                              ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Mantén presionado',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: colors.onErrorContainer,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          _LocationCard(locationService: _locationService),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              leading: const Icon(Icons.contact_emergency),
              title: const Text('Contacto de confianza'),
              subtitle: Text(
                _trustedContact == null
                    ? 'Aún no has configurado un número'
                    : '${_trustedContactChannel == EmergencyService.whatsappChannel ? 'WhatsApp' : 'SMS'} • $_trustedContact',
              ),
              trailing: const Icon(Icons.edit),
              onTap: _configureTrustedContact,
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _isOpeningNearbyHelp ? null : _openNearbyHelp,
            icon: _isOpeningNearbyHelp
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.near_me),
            label: const Text('Buscar ayuda cercana'),
          ),
          const SizedBox(height: 24),
          Text(
            'Líneas de emergencia',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Elige el organismo adecuado para la situación.',
          ),
          const SizedBox(height: 12),
          ...EmergencyService.officialContacts.map(
            (EmergencyContact contact) => Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: ListTile(
                leading: CircleAvatar(child: Icon(contact.icon)),
                title: Text(contact.name),
                subtitle: Text('${contact.description}\nLínea ${contact.phone}'),
                isThreeLine: true,
                trailing: IconButton.filledTonal(
                  tooltip: 'Llamar a ${contact.name}',
                  icon: const Icon(Icons.call),
                  onPressed: () => _callEmergency(contact),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Importante: el SOS abre SMS o WhatsApp, según tu elección, con el texto y la ubicación preparados. El usuario confirma el envío desde el dispositivo.',
            style: TextStyle(fontSize: 12),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}

class _LocationCard extends StatelessWidget {
  const _LocationCard({required this.locationService});

  final LocationService locationService;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<LocationState>(
      valueListenable: locationService.stateListenable,
      builder: (BuildContext context, LocationState state, _) {
        final Position? position = state.position;

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Icon(Icons.my_location),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const Text(
                        'Tu ubicación',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      if (state.isLoading && position == null)
                        const Text('Obteniendo coordenadas...')
                      else if (position != null)
                        Text(
                          '${position.latitude.toStringAsFixed(6)}, '
                          '${position.longitude.toStringAsFixed(6)}',
                        )
                      else
                        Text(
                          state.errorMessage ??
                              'La ubicación todavía no está disponible.',
                        ),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: 'Actualizar ubicación',
                  onPressed: state.isLoading ? null : locationService.refresh,
                  icon: const Icon(Icons.refresh),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
