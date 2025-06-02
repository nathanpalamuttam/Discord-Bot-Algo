#include <iostream>
#include <string>
#include <curl/curl.h>
#include "json.hpp"

using json = nlohmann::json;

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

int main() {
    json result = get_vwap_from_server("AAPL", "2025-06-01", "2025-06-06");
    std::cout << "📈 VWAP response:\n" << result.dump(2) << std::endl;
    return 0;
}
