import 'package:flutter/material.dart';

class EmergencyContact {
  const EmergencyContact({
    required this.name,
    required this.phone,
    required this.description,
    required this.icon,
  });

  final String name;
  final String phone;
  final String description;
  final IconData icon;
}
