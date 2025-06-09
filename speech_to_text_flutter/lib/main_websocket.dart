import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

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
    late WebSocketChannel channel;
    String _transcription = '';
    bool _isRecognizing = false;
    String _statusMessage = 'Click Start to begin...';

    @override
    void initState() {
    super.initState();
    initializeWebSocket();
    print('Initialized VoiceToTextPageState');
    }

    void initializeWebSocket() {
    channel = WebSocketChannel.connect(Uri.parse('ws://localhost:5000'));
    channel.stream.listen(
        (message) {
        print('Received message: $message at ${DateTime.now()}');
        final data = jsonDecode(message);
        if (data is Map && data.containsKey('event')) {
            if (data['event'] == 'transcription') {
            final transcriptionData = data['data'];
            if (transcriptionData is Map && transcriptionData.containsKey('text')) {
                setState(() {
                if (transcriptionData['append'] == true) {
                    _transcription = _transcription.isEmpty
                        ? transcriptionData['text']
                        : '$_transcription ${transcriptionData['text']}';
                } else {
                    _transcription = transcriptionData['text'];
                }
                print('Updated _transcription: $_transcription at ${DateTime.now()}');
                });
            }
            } else if (data['event'] == 'status') {
            final statusData = data['data'];
            if (statusData is Map && statusData.containsKey('isRecognizing')) {
                setState(() {
                _isRecognizing = statusData['isRecognizing'];
                _statusMessage = statusData['message'] ?? (_isRecognizing ? 'Recognizing...' : 'Ready');
                print('Updated _statusMessage: $_statusMessage');
                });
            }
            }
        }
        },
        onError: (error) {
        print('WebSocket Error: $error');
        setState(() {
            _statusMessage = 'WebSocket error';
        });
        },
        onDone: () {
        print('WebSocket Closed');
        setState(() {
            _statusMessage = 'Disconnected from server';
        });
        },
    );
    }

    void _toggleRecognition() {
    if (_isRecognizing) {
        print('Sending stop_recognition');
        channel.sink.add(jsonEncode({'event': 'stop_recognition'}));
    } else {
        print('Sending start_recognition');
        channel.sink.add(jsonEncode({'event': 'start_recognition'}));
    }
    }

    @override
    void dispose() {
    channel.sink.close();
    super.dispose();
    print('Disposed VoiceToTextPageState');
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
                onPressed: _toggleRecognition,
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
                child: SingleChildScrollView(
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
            ),
        ],
        ),
    );
    }
}