#include <iostream>
#include <fstream>
#include <string>
#include <thread>
#include <chrono>
#include "json.hpp"       // make sure json.hpp is in the same folder
#include "strategy.hpp"   // declares apply_strategy()

const std::string PIPE_PATH = "/tmp/trade_pipe";

void process_json_line(const std::string& line) {
    try {
        nlohmann::json j = nlohmann::json::parse(line);
        std::cout << "✅ Received: " << j.dump(2) << std::endl;
        apply_strategy(j);  // Call strategy logic
        std::cout << "Strategy over";
    } catch (nlohmann::json::parse_error& e) {
        std::cerr << "❌ JSON parse error: " << e.what() << std::endl;
    }
}

int main() {
    std::cout << "📥 Waiting for data on " << PIPE_PATH << "...\n";

    while (true) {
        std::ifstream pipe(PIPE_PATH);
        if (!pipe.is_open()) {
            std::cerr << "❌ Failed to open pipe — retrying...\n";
            std::this_thread::sleep_for(std::chrono::seconds(1));
            continue;
        }

        std::string line;
        while (std::getline(pipe, line)) {
            std::cout << line;
            process_json_line(line);
        }

        std::cout << "⚠️ Pipe closed by writer — reopening...\n";
    }

    return 0;
}
