// Apple Live Text for the benchmark: VisionKit's ImageAnalyzer, the API
// behind Live Text in Preview, Photos and Safari on the Mac.
// Prints one JSON line with facts, then for each image path read on stdin,
// prints one JSON line {"text": "..."} (the analyzer's own transcript and
// reading order) or {"error": "..."}.
import AppKit
import Foundation
import VisionKit

func emit(_ obj: Any) {
    let data = try! JSONSerialization.data(withJSONObject: obj, options: [])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write("\n".data(using: .utf8)!)
}

@main
struct LiveTextServer {
    static func main() async {
        emit(["os": ProcessInfo.processInfo.operatingSystemVersionString,
              "languages": ImageAnalyzer.supportedTextRecognitionLanguages])
        let analyzer = ImageAnalyzer()
        var config = ImageAnalyzer.Configuration([.text])
        config.locales = ["ar-SA"]
        while let line = readLine() {
            let path = line.trimmingCharacters(in: .whitespacesAndNewlines)
            if path.isEmpty { continue }
            guard let img = NSImage(contentsOfFile: path) else {
                emit(["error": "cannot read image \(path)"])
                continue
            }
            do {
                let analysis = try await analyzer.analyze(img, orientation: .up, configuration: config)
                emit(["text": analysis.transcript])
            } catch {
                emit(["error": "\(error)"])
            }
        }
    }
}
