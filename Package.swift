// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "JiulianSuperPasswordTool",
    platforms: [.macOS(.v13)],
    products: [
        .executable(name: "JiulianSuperPasswordTool", targets: ["JiulianSuperPasswordTool"])
    ],
    targets: [
        .executableTarget(name: "JiulianSuperPasswordTool")
    ]
)
