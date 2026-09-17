import 'dart:async';

import 'package:arcgis_maps/arcgis_maps.dart';
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'models/app_user.dart';
import 'models/activity_survey.dart';
import 'pages/activity_survey_page.dart';
import 'pages/login_page.dart';
import 'pages/mapa_page.dart';
import 'pages/profile_page.dart';
import 'pages/recommendations_page.dart';
import 'pages/reportes_page.dart';
import 'pages/rutas_seguras_page.dart';
import 'services/activity_survey_service.dart';
import 'services/supabase_service.dart';
import 'services/storage_service.dart';
import 'services/auth_service.dart';
import 'widgets/connectivity_banner.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await dotenv.load(fileName: '.env');

  // Configurar la API Key de ArcGIS
  final String arcgisApiKey = dotenv.get('ARCGIS_API_KEY', fallback: '');
  if (arcgisApiKey.isNotEmpty) {
    ArcGISEnvironment.apiKey = arcgisApiKey;
  }

  await SupabaseService.instance.initialize();
  await AuthService.instance.initialize();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'App Turismo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      debugShowCheckedModeBanner: false,
      builder: (context, child) => ConnectivityBanner(child: child!),
      home: const AuthGate(),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  final AuthService _authService = AuthService.instance;
  AppUser? _lastUser;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<AppUser?>(
      valueListenable: _authService.currentUserListenable,
      builder: (BuildContext context, AppUser? user, _) {
        if (user == null) {
          if (_lastUser != null) {
            _lastUser = null;
            WidgetsBinding.instance.addPostFrameCallback((_) {
              unawaited(StorageService.instance.clearForSignOut());
              unawaited(ActivitySurveyService.instance.clearForSignOut());
            });
          }
          return const LoginPage();
        }

        if (_lastUser?.id != user.id) {
          _lastUser = user;
        }

        return AuthenticatedApp(user: user);
      },
    );
  }
}

class AuthenticatedApp extends StatefulWidget {
  const AuthenticatedApp({
    super.key,
    required this.user,
  });

  final AppUser user;

  @override
  State<AuthenticatedApp> createState() => _AuthenticatedAppState();
}

class _AuthenticatedAppState extends State<AuthenticatedApp> {
  late Future<void> _initialization;
  final ActivitySurveyService _surveyService = ActivitySurveyService.instance;

  @override
  void initState() {
    super.initState();
    _initialization = Future.wait<void>(<Future<void>>[
      StorageService.instance.initializeForUser(widget.user.id),
      _surveyService.initializeForUser(widget.user.id),
    ]);
  }

  @override
  void didUpdateWidget(covariant AuthenticatedApp oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.user.id != widget.user.id) {
      setState(() {
        _initialization = Future.wait<void>(<Future<void>>[
          StorageService.instance.initializeForUser(widget.user.id),
          _surveyService.initializeForUser(widget.user.id),
        ]);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _initialization,
      builder: (BuildContext context, AsyncSnapshot<void> snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          );
        }

        if (snapshot.hasError) {
          return Scaffold(
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    const Icon(Icons.error_outline, size: 48, color: Colors.red),
                    const SizedBox(height: 16),
                    const Text(
                      'No se pudieron cargar tus datos. Intenta nuevamente.',
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () {
                        setState(() {
                          _initialization = StorageService.instance
                              .initializeForUser(widget.user.id);
                        });
                      },
                      child: const Text('Reintentar'),
                    ),
                  ],
                ),
              ),
            ),
          );
        }

        return ValueListenableBuilder<ActivitySurvey?>(
          valueListenable: _surveyService.surveyListenable,
          builder: (BuildContext context, ActivitySurvey? survey, _) {
            if (survey == null) {
              return ActivitySurveyPage(
                onCompleted: () {
                  setState(() {});
                },
              );
            }

            return MainScaffold(
              onLogout: AuthService.instance.logout,
            );
          },
        );
      },
    );
  }
}

class MainScaffold extends StatefulWidget {
  const MainScaffold({
    super.key,
    this.onLogout,
  });

  final VoidCallback? onLogout;

  @override
  State<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends State<MainScaffold> {
  int _selectedIndex = 0;
  late final List<Widget> _tabPages;
  late final List<BottomNavigationBarItem> _navigationItems;
  final PageStorageBucket _pageStorageBucket = PageStorageBucket();

  static const List<_NavigationTab> _tabs = <_NavigationTab>[
    _NavigationTab(
      label: 'Mapa',
      icon: Icons.map,
      page: MapaPage(
        key: PageStorageKey<String>('MapaPage'),
      ),
    ),
    _NavigationTab(
      label: 'Rutas Seguras',
      icon: Icons.route,
      page: RutasSegurasPage(
        key: PageStorageKey<String>('RutasSegurasPage'),
      ),
    ),
    _NavigationTab(
      label: 'Reportes',
      icon: Icons.report,
      page: ReportesPage(
        key: PageStorageKey<String>('ReportesPage'),
      ),
    ),
    _NavigationTab(
      label: 'Recomendaciones',
      icon: Icons.auto_awesome,
      page: RecommendationsPage(
        key: PageStorageKey<String>('RecommendationsPage'),
      ),
    ),
    _NavigationTab(
      label: 'Perfil',
      icon: Icons.person,
      page: ProfilePage(
        key: PageStorageKey<String>('ProfilePage'),
      ),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _tabPages =
        _tabs.map((tab) => tab.page).toList(growable: false);
    _navigationItems = _tabs
        .map(
          (tab) => BottomNavigationBarItem(
            icon: Icon(tab.icon),
            label: tab.label,
          ),
        )
        .toList(growable: false);
  }

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final _NavigationTab currentTab = _tabs[_selectedIndex];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(currentTab.label),
        actions: <Widget>[
          if (widget.onLogout != null)
            IconButton(
              icon: const Icon(Icons.logout),
              tooltip: 'Cerrar sesión',
              onPressed: widget.onLogout,
            ),
        ],
      ),
      body: PageStorage(
        bucket: _pageStorageBucket,
        child: IndexedStack(
          index: _selectedIndex,
          children: _tabPages,
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        items: _navigationItems,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }
}

class _NavigationTab {
  const _NavigationTab({
    required this.label,
    required this.icon,
    required this.page,
  });

  final String label;
  final IconData icon;
  final Widget page;
}