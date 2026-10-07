// Apple Vision text recognition server for the benchmark.
// Prints one JSON line with facts, then for each image path read on stdin,
// prints one JSON line {"observations": [{text, x, y, w, h, conf}]} with
// normalized boxes (origin bottom-left), or {"error": "..."}.
import Foundation
import Vision
import ImageIO

func emit(_ obj: Any) {
    let data = try! JSONSerialization.data(withJSONObject: obj, options: [])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write("\n".data(using: .utf8)!)
}

let probe = VNRecognizeTextRequest()
probe.recognitionLevel = .accurate
let langs = (try? probe.supportedRecognitionLanguages()) ?? []
emit(["os": ProcessInfo.processInfo.operatingSystemVersionString,
      "revision": probe.revision,
      "languages": langs])

while let line = readLine() {
    let path = line.trimmingCharacters(in: .whitespacesAndNewlines)
    if path.isEmpty { continue }
    let url = URL(fileURLWithPath: path)
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        emit(["error": "cannot read image \(path)"])
        continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["ar-SA"]
    req.usesLanguageCorrection = true
    do {
        try VNImageRequestHandler(cgImage: img, options: [:]).perform([req])
        var out: [[String: Any]] = []
        for obs in req.results ?? [] {
            guard let cand = obs.topCandidates(1).first else { continue }
            let b = obs.boundingBox
            out.append(["text": cand.string, "x": b.origin.x, "y": b.origin.y,
                        "w": b.size.width, "h": b.size.height, "conf": cand.confidence])
        }
        emit(["observations": out])
    } catch {
        emit(["error": "\(error)"])
    }
}
