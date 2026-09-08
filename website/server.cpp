#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
using Socket = SOCKET;
constexpr Socket invalid_socket = INVALID_SOCKET;
#else
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
using Socket = int;
constexpr Socket invalid_socket = -1;
#endif

namespace {

void close_socket(Socket socket) {
#ifdef _WIN32
    closesocket(socket);
#else
    close(socket);
#endif
}

bool send_all(Socket socket, const std::string& data) {
    std::size_t sent = 0;
    while (sent < data.size()) {
#ifdef _WIN32
        const int result = send(socket, data.data() + sent, static_cast<int>(data.size() - sent), 0);
#else
        const ssize_t result = send(socket, data.data() + sent, data.size() - sent, 0);
#endif
        if (result <= 0) return false;
        sent += static_cast<std::size_t>(result);
    }
    return true;
}

std::string content_type(const std::filesystem::path& path) {
    const std::string extension = path.extension().string();
    if (extension == ".html") return "text/html; charset=utf-8";
    if (extension == ".css") return "text/css; charset=utf-8";
    if (extension == ".js") return "text/javascript; charset=utf-8";
    if (extension == ".json") return "application/json";
    if (extension == ".exe") return "application/vnd.microsoft.portable-executable";
    return "application/octet-stream";
}

void reply(Socket socket, int status, const std::string& type, const std::string& body, bool download = false) {
    std::ostringstream headers;
    headers << "HTTP/1.1 " << status << (status == 200 ? " OK" : status == 404 ? " Not Found" : " Bad Request") << "\r\n"
            << "Content-Type: " << type << "\r\n"
            << "Content-Length: " << body.size() << "\r\n"
            << "X-Content-Type-Options: nosniff\r\n"
            << "Cache-Control: public, max-age=300\r\n";
    if (download) headers << "Content-Disposition: attachment; filename=\"KSA ENGINE.exe\"\r\n";
    headers << "Connection: close\r\n\r\n";
    send_all(socket, headers.str() + body);
}

void handle(Socket socket, const std::filesystem::path& root) {
    char buffer[8192]{};
#ifdef _WIN32
    const int received = recv(socket, buffer, sizeof(buffer) - 1, 0);
#else
    const ssize_t received = recv(socket, buffer, sizeof(buffer) - 1, 0);
#endif
    if (received <= 0) return;
    std::istringstream request(std::string(buffer, static_cast<std::size_t>(received)));
    std::string method;
    std::string target;
    std::string protocol;
    request >> method >> target >> protocol;
    if (method != "GET" || target.empty() || target.front() != '/') {
        reply(socket, 400, "text/plain; charset=utf-8", "Bad Request\n");
        return;
    }
    const std::size_t query = target.find('?');
    if (query != std::string::npos) target.resize(query);
    if (target == "/") target = "/index.html";
    std::filesystem::path relative = std::filesystem::path(target.substr(1));
    if (relative.empty() || relative.is_absolute() || relative.lexically_normal() != relative || relative.string().find("..") != std::string::npos) {
        reply(socket, 400, "text/plain; charset=utf-8", "Invalid path\n");
        return;
    }
    const std::filesystem::path file = root / relative;
    if (!std::filesystem::is_regular_file(file)) {
        reply(socket, 404, "text/plain; charset=utf-8", "Not Found\n");
        return;
    }
    std::ifstream input(file, std::ios::binary);
    const std::string body((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
    reply(socket, 200, content_type(file), body, file.extension() == ".exe");
}

}  // namespace

int main(int argc, char* argv[]) {
    int port = 8080;
    std::filesystem::path root = std::filesystem::current_path() / "website";
    for (int index = 1; index < argc; ++index) {
        const std::string argument = argv[index];
        if (argument == "--port" && index + 1 < argc) port = std::stoi(argv[++index]);
        else if (argument == "--root" && index + 1 < argc) root = argv[++index];
        else if (argument == "--help") {
            std::cout << "KSA independent download server\nUsage: ksa_download_server [--root PATH] [--port N]\n";
            return 0;
        } else {
            std::cerr << "Unknown option: " << argument << '\n';
            return 2;
        }
    }
    if (!std::filesystem::is_directory(root)) {
        std::cerr << "Website root does not exist: " << root << '\n';
        return 1;
    }
#ifdef _WIN32
    WSADATA data{};
    if (WSAStartup(MAKEWORD(2, 2), &data) != 0) return 1;
#endif
    const Socket server = socket(AF_INET, SOCK_STREAM, 0);
    if (server == invalid_socket) return 1;
    int reuse = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, reinterpret_cast<const char*>(&reuse), sizeof(reuse));
    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_ANY);
    address.sin_port = htons(static_cast<std::uint16_t>(port));
    if (bind(server, reinterpret_cast<const sockaddr*>(&address), sizeof(address)) != 0 || listen(server, 16) != 0) {
        close_socket(server);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }
    std::cout << "KSA download server: http://localhost:" << port << "\nRoot: " << root << '\n';
    while (true) {
        const Socket client = accept(server, nullptr, nullptr);
        if (client == invalid_socket) break;
        handle(client, root);
        close_socket(client);
    }
    close_socket(server);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
