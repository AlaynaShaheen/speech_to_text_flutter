import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

void main() {
    runApp(const MyApp());
}

class MyApp extends StatelessWidget {
    const MyApp({super.key});

    @override
    Widget build(BuildContext context) {
    return MaterialApp(
        title: 'Real-Time Voice to Text',
        theme: ThemeData(primarySwatch: Colors.blue),
        home: const VoiceToTextPage(),
    );
    }
}

class VoiceToTextPage extends StatefulWidget {
    const VoiceToTextPage({super.key});

    @override
    State<VoiceToTextPage> createState() => _VoiceToTextPageState();
}

class _VoiceToTextPageState extends State<VoiceToTextPage> {
    late IO.Socket socket;
    String _transcription = '';
    bool _isRecognizing = false;
    String _statusMessage = 'Click Start to begin...';
    bool _isButtonEnabled = true;

    @override
    void initState() {
    super.initState();
    initializeSocket();
    print('Initialized VoiceToTextPageState at ${DateTime.now()}');
    }

    void initializeSocket() {
    socket = IO.io('http://localhost:5000', <String, dynamic>{
        'transports': ['websocket'],
        'autoConnect': true,
        'forceNew': false,
        'reconnection': true,
        'reconnectionAttempts': 5,
        'reconnectionDelay': 1000,
        'timeout': 10000,
        'namespace': '/',
    });

    socket.connect();

    socket.onConnect((_) {
        print('SocketIO: Connected to server at ${DateTime.now()}');
        setState(() {
        _statusMessage = 'Connected to server';
        });
    });

    socket.onDisconnect((_) {
        print('SocketIO: Disconnected from server at ${DateTime.now()}');
        setState(() {
        _statusMessage = 'Disconnected from server';
        _isRecognizing = false;
        _isButtonEnabled = true;
        });
    });

    socket.on('transcription', (data) {
        final receiveTime = DateTime.now();
        print('Received transcription: $data at $receiveTime');
        if (data is Map && data.containsKey('text')) {
        final newText = data['text'] as String;
        setState(() {
            if (data['append'] == true) {
            _transcription = _transcription.isEmpty ? newText : '$_transcription $newText';
            } else {
            _transcription = newText;
            }
            print('Updated _transcription: $_transcription at ${DateTime.now()} (delay: ${DateTime.now().difference(receiveTime).inMilliseconds}ms)');
        });
        } else {
        print('Invalid transcription data: $data at ${DateTime.now()}');
        }
    });

    socket.on('status', (data) {
        print('Received status: $data at ${DateTime.now()}');
        setState(() {
        if (data is Map && data.containsKey('isRecognizing')) {
            _isRecognizing = data['isRecognizing'];
            _statusMessage = data['message'] ?? (_isRecognizing ? 'Recognizing...' : 'Ready');
            _isButtonEnabled = true;
            print('Updated _statusMessage: $_statusMessage at ${DateTime.now()}');
        } else {
            print('Invalid status data: $data at ${DateTime.now()}');
        }
        });
    });

    socket.onConnectError((error) {
        print('SocketIO Connect Error: $error at ${DateTime.now()}');
        setState(() {
        _statusMessage = 'Connection error';
        _isButtonEnabled = true;
        });
    });

    socket.onError((error) {
        print('SocketIO Error: $error at ${DateTime.now()}');
        setState(() {
        _statusMessage = 'Socket error';
        _isButtonEnabled = true;
        });
    });

    socket.onConnectTimeout((data) {
        print('SocketIO Connect Timeout: $data at ${DateTime.now()}');
        setState(() {
        _statusMessage = 'Connection timeout';
        _isButtonEnabled = true;
        });
    });

    socket.onAny((event, data) {
        print('SocketIO Event: $event with data: $data at ${DateTime.now()}');
    });
    }

    void _toggleRecognition() {
    if (!_isButtonEnabled) return;
    setState(() {
        _isButtonEnabled = false;
    });
    if (_isRecognizing) {
        print('Sending stop_recognition at ${DateTime.now()}');
        socket.emit('stop_recognition');
    } else {
        print('Sending start_recognition at ${DateTime.now()}');
        socket.emit('start_recognition');
    }
    Future.delayed(const Duration(milliseconds: 500), () {
        if (mounted) {
        setState(() {
            _isButtonEnabled = true;
        });
        }
    });
    }

    @override
    void dispose() {
    socket.disconnect();
    socket.dispose();
    super.dispose();
    print('Disposed VoiceToTextPageState at ${DateTime.now()}');
    }

    @override
    Widget build(BuildContext context) {
    print('Building VoiceToTextPage with _transcription: $_transcription at ${DateTime.now()}');
    return Scaffold(
        appBar: AppBar(title: const Text('Real-Time Voice to Text')),
        body: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
            Padding(
            padding: const EdgeInsets.all(20.0),
            child: ElevatedButton(
                onPressed: _isButtonEnabled ? _toggleRecognition : null,
                style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                backgroundColor: _isRecognizing ? Colors.red : Colors.blue,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(5)),
                ),
                child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                    Icon(
                    _isRecognizing ? Icons.mic_off : Icons.mic,
                    size: 24,
                    color: Colors.white,
                    ),
                    const SizedBox(width: 8),
                    Text(
                    _isRecognizing ? 'Stop' : 'Start',
                    style: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
                ],
                ),
            ),
            ),
            Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0),
            child: Text(
                _statusMessage,
                style: const TextStyle(fontSize: 14, color: Colors.grey),
                textAlign: TextAlign.center,
            ),
            ),
            const SizedBox(height: 10),
            Expanded(
            child: Container(
                margin: const EdgeInsets.all(20.0),
                padding: const EdgeInsets.all(10.0),
                decoration: BoxDecoration(
                border: Border.all(color: Colors.grey),
                borderRadius: BorderRadius.circular(5),
                color: Colors.white,
                ),
                child: Text(
                _transcription.isEmpty ? 'No transcriptions yet...' : _transcription,
                style: const TextStyle(
                    fontSize: 16,
                    color: Colors.black,
                    height: 1.5,
                ),
                ),
            ),
            ),
        ],
        ),
    );
    }
}