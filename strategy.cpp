#include <iostream>
#include <string>
#include <curl/curl.h>
#include "json.hpp"
#include "strategy.hpp"

using json = nlohmann::json;

// Callback for writing HTTP response to string
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* buffer) {
    size_t totalSize = size * nmemb;
    buffer->append((char*)contents, totalSize);
    return totalSize;
}

json get_vwap_from_server(const std::string& symbol, const std::string& from, const std::string& to) {
    CURL* curl = curl_easy_init();
    std::string readBuffer;

    if (curl) {
        json payload = {
            {"symbol", symbol},
            {"from", from},
            {"to", to}
        };

        std::string payloadStr = payload.dump();
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        curl_easy_setopt(curl, CURLOPT_URL, "http://localhost:5000/vwap");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payloadStr.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        CURLcode res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }

    return json::parse(readBuffer);
}

void apply_strategy(const nlohmann::json& signal) {
    std::cout << "📊 Applying strategy to signal..." << std::endl;

    try {
        std::string symbol = signal.value("symbol", "UNKNOWN");
        double price = signal.value("limitPrice", 0.0);
        std::string exp_date = signal.value("expiration", "");
        std::string from = exp_date;  // for now, use expiration as both start/end
        std::string to = exp_date;

        json vwap_data = get_vwap_from_server(symbol, from, to);
        double vwap = vwap_data.value("vwap", 0.0);

        std::cout << "🔍 " << symbol << " Limit Price: " << price << " | VWAP: " << vwap << std::endl;

        if (price < vwap) {
            std::cout << "✅ Price is below VWAP — good entry.\n";
        } else {
            std::cout << "❌ Price is above VWAP — avoid trade.\n";
        }

    } catch (const std::exception& e) {
        std::cerr << "❌ Strategy failed: " << e.what() << std::endl;
    }
}
