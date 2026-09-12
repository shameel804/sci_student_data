import 'dart:convert';
import 'dart:io';
import 'Constants.dart';

void main() async {
  bool hasError = false;
  
  for (var entry in Constants.allTypes.entries) {
    String course = entry.key;
    List<Map<String, dynamic>> topics = entry.value;
    
    for (var topic in topics) {
      String id = topic['id'];
      
      // Paths to check
      String version = 'v1';
      String quizPath = '$version/$course/$id.json';
      String learnPath = '$version/$course/learn/$id.json';
      String projectPath = '$version/$course/projects/$id.json';
      
      List<String> pathsToCheck = [quizPath, learnPath, projectPath];
      
      for (String path in pathsToCheck) {
        File file = File(path);
        if (!await file.exists()) {
          print('❌ MISSING FILE: $path');
          hasError = true;
          continue;
        }
        
        // Optional: check if the JSON inside learn file has the correct ID
        if (path.contains('/learn/')) {
           try {
              String content = await file.readAsString();
              var json = jsonDecode(content);
              if (json is Map) {
                if (json['topicId'] != id) {
                   print('⚠️ ID MISMATCH IN $path: Expected topicId=$id, got ${json['topicId']}');
                   hasError = true;
                }
              }
           } catch(e) {
              print('❌ ERROR PARSING $path: $e');
              hasError = true;
           }
        }
      }
    }
  }
  
  if (!hasError) {
    print('\n✅ All files are present and IDs match perfectly.');
  } else {
    print('\n⚠️ Verification failed with errors above.');
  }
}
